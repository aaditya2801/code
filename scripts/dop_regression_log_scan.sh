#!/usr/bin/env bash
# Scan ALL pods in dop namespace (last 30m) — no hardcoded service list.
# Run: bash dop_regression_log_scan.sh

set -uo pipefail

NS="${NS:-dop}"
SINCE="${SINCE:-30m}"
OUT_DIR="${OUT_DIR:-./dop-log-scan-$(date +%Y%m%d-%H%M%S)}"

ERROR_PAT='ERROR|Exception|FATAL|Failed|failure|timeout|refused|Unavailable|500|503|404|NoClassDefFoundError|BeanCreationException|UnknownHost|planned|Planned|Active|context|activation|inventory|CFS|regression|rollback|stuck|reject'

mkdir -p "$OUT_DIR"/{logs,summary}

echo "=== dop full namespace scan ==="
echo "Namespace : $NS"
echo "Since     : $SINCE"
echo "Output    : $OUT_DIR"
echo

echo "[1/7] All pods..."
kubectl get pods -n "$NS" -o wide | tee "$OUT_DIR/summary/pods.txt"
kubectl get pods -n "$NS" --no-headers | awk '$3!="Running" && $3!="Completed" {print}' | tee "$OUT_DIR/summary/not_running_pods.txt"

echo
echo "[2/7] All deployments / statefulsets / jobs..."
kubectl get deploy,sts,ds,job,cronjob -n "$NS" 2>/dev/null | tee "$OUT_DIR/summary/workloads.txt"
kubectl get deploy -n "$NS" -o custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,DESIRED:.spec.replicas 2>/dev/null | tee "$OUT_DIR/summary/deployments.txt"

echo
echo "[3/7] All services + ingress..."
kubectl get svc -n "$NS" 2>/dev/null | tee "$OUT_DIR/summary/services.txt"
kubectl get ingress -n "$NS" -o custom-columns=NAME:.metadata.name,HOSTS:.spec.rules[*].host 2>/dev/null | tee "$OUT_DIR/summary/ingress.txt"

echo
echo "[4/7] Recent events..."
kubectl get events -n "$NS" --sort-by='.lastTimestamp' 2>/dev/null | tail -300 | tee "$OUT_DIR/summary/events.txt"

echo
echo "[5/7] Fetch logs — ALL pods in $NS (last $SINCE)..."
mapfile -t ALL_PODS < <(kubectl get pods -n "$NS" --no-headers -o custom-columns=NAME:.metadata.name,STATUS:.status.phase 2>/dev/null | awk '{print $1}')
TOTAL=${#ALL_PODS[@]}
i=0
for pname in "${ALL_PODS[@]}"; do
  i=$((i + 1))
  echo "  [$i/$TOTAL] $pname"
  kubectl logs -n "$NS" "$pname" --all-containers=true --since="$SINCE" --timestamps=true \
    > "$OUT_DIR/logs/${pname}.log" 2>&1 || true
  # crashed/restarted pods — previous container logs bhi
  status=$(kubectl get pod "$pname" -n "$NS" --no-headers 2>/dev/null | awk '{print $3}')
  if [[ "$status" =~ ^(Error|CrashLoopBackOff|Failed|Unknown)$ ]]; then
    kubectl logs -n "$NS" "$pname" --all-containers=true --previous --timestamps=true \
      > "$OUT_DIR/logs/${pname}.previous.log" 2>&1 || true
  fi
done

echo
echo "[6/7] Init container failures..."
for pname in "${ALL_PODS[@]}"; do
  inits=$(kubectl get pod "$pname" -n "$NS" -o jsonpath='{range .status.initContainerStatuses[*]}{.name}{" "}{.state.terminated.reason}{"\n"}{end}' 2>/dev/null)
  if echo "$inits" | grep -qiE 'error|crash|fail|oom'; then
    echo "  init fail: $pname"
    kubectl logs -n "$NS" "$pname" --all-containers=true --timestamps=true \
      > "$OUT_DIR/logs/${pname}.init.log" 2>&1 || true
  fi
done

echo
echo "[7/7] Analyze all collected logs..."
{
  echo "=== NAMESPACE: $NS | SINCE: $SINCE | PODS SCANNED: $TOTAL ==="
  echo

  echo "=== NOT RUNNING PODS ==="
  cat "$OUT_DIR/summary/not_running_pods.txt"
  echo

  echo "=== DEPLOYMENTS NOT FULLY READY ==="
  awk 'NR>1 && ($2 != $3 || $2 == "<none>") {print}' "$OUT_DIR/summary/deployments.txt"
  echo

  echo "=== TOP ERROR LINES (all pods) ==="
  grep -Ehi "$ERROR_PAT" "$OUT_DIR"/logs/*.log 2>/dev/null \
    | sed "s|$OUT_DIR/logs/||" | head -400
  echo

  echo "=== PLANNED / ACTIVE / CONTEXT / CFS ==="
  grep -Ehi 'planned|Active|context|inventory|CFS|state transition|lifecycle|regression' "$OUT_DIR"/logs/*.log 2>/dev/null \
    | sed "s|$OUT_DIR/logs/||" | head -200
  echo

  echo "=== ERROR COUNT BY POD (top 30) ==="
  for f in "$OUT_DIR"/logs/*.log; do
    [ -f "$f" ] || continue
    c=$(grep -Eci 'ERROR|Exception|Failed|FATAL' "$f" 2>/dev/null || echo 0)
    [ "$c" -gt 0 ] && printf "%5d  %s\n" "$c" "$(basename "$f")"
  done | sort -rn | head -30
  echo

  echo "=== PODS WITH ZERO LOGS (may be idle or failed fetch) ==="
  for f in "$OUT_DIR"/logs/*.log; do
    [ -f "$f" ] || continue
    [ ! -s "$f" ] && echo "  empty: $(basename "$f")"
  done
  echo

  echo "=== RECENT EVENTS (warn/fail/error) ==="
  grep -iE 'warn|fail|error|backoff|unhealthy|evict|kill|oom' "$OUT_DIR/summary/events.txt" | tail -50
} | tee "$OUT_DIR/summary/ANALYSIS.txt"

echo
echo "Done. Scanned $TOTAL pods in namespace $NS"
echo "Read first : $OUT_DIR/summary/ANALYSIS.txt"
echo "All logs   : $OUT_DIR/logs/"
echo
echo "Tarball for sharing:"
echo "  tar -czf dop-scan.tgz $OUT_DIR && ls -lh dop-scan.tgz"
