"""Edit invoice PDF precisely - preserve Credit, Due Date, Buyer/Shipped labels."""

import fitz
from pathlib import Path

SRC = Path(r"c:\Users\aadityat\Downloads\Invoice_HO-2627-7434.pdf")
OUT = Path(r"c:\Users\aadityat\Downloads\Invoice_HO-2627-7434_DEMO.pdf")

BUYER_LINES = [
    ("M/S MAP ENTERPRISES", "hebo", 12),
    ("C-40, KARAMCHARI AWAS COLONY, NEAR PANT NAGAR,", "helv", 9),
    ("GWALIOR- 4740002 M.P", "helv", 9),
    ("Gwalior - Madhya Pradesh", "helv", 9),
    ("PIN :474002", "helv", 9),
    ("Email :mkbmap@gmail.com", "helv", 9),
    ("GSTIN :23AECPB8380C1Z1", "hebo", 9),
    ("GST Type :Regular", "helv", 9),
    ("E-Mail ID: mkbmap@gmail.com", "helv", 9),
]

SHIPPED_LINES = [
    ("M/S MAP ENTERPRISES", "hebo", 12),
    ("C-40, KARAMCHARI AWAS COLONY, NEAR PANT NAGAR,", "helv", 9),
    ("GWALIOR- 4740002 M.P", "helv", 9),
    ("Gwalior - Madhya Pradesh", "helv", 9),
    ("PIN :474002", "helv", 9),
    ("GSTIN :23AECPB8380C1Z1", "hebo", 9),
    ("POS : Madhya Pradesh [State Code : 23]", "helv", 9.5),
    ("Contact Person : MAHENDRA KUMAR BHARDWAJ", "hebo", 9.5),
    ("Mobile : 9685985078", "hebo", 9.5),
]

OLD_BUYER = [
    "C P Vaswani Distribution and Allied",
    "Services LLP",
    "Shop 1 Floor, Ridham Building, 59, Forbes St, Above",
    "Raymond, Kala Ghoda, FORT, Mumbai, Maharashtra",
    "Mumbai - Maharashtra",
    "PIN :400023",
    "Tel :0091,22,40633939,22844303,22842984",
    "Email :sharad.salunke@cpvaswani.com",
    "GSTIN :27AASFC5826A1ZG",
    "GST Type :Regular",
    "E-Mail ID: sharad.salunke@cpvaswani.com",
]

OLD_SHIPPED = [
    "SSE INFRASTRUCTURE AND",
    "DEVELOPERS PRIVATE LIMITED",
    "Sawai Man Singh Hospital Jawaharlal Nehru Marg",
    "Jaipur",
    "Jaipur, Rajasthan-302004",
    "JAYPUR - Rajasthan",
    "PIN :302004",
    "GSTIN :27AASFC5826A1ZG",
    "POS : Maharashtra [State Code : 27]",
    "Contact Person : Mr. Sharad Salunke",
    "Mobile : 9769800491",
]

X = 21.26


def redact_left_column_strings(page: fitz.Page, strings: list[str]) -> None:
    """Redact only matches in left column (x < 240) to avoid damaging right-side fields."""
    for s in strings:
        for rect in page.search_for(s):
            if rect.x0 < 240:
                pad = fitz.Rect(rect.x0 - 1, rect.y0 - 0.5, rect.x1 + 1, rect.y1 + 0.5)
                page.add_redact_annot(pad, fill=(1, 1, 1))
    page.apply_redactions()


def write_block(page: fitz.Page, lines: list[tuple[str, str, float]], start_y: float) -> None:
    y = start_y
    for text, font, size in lines:
        page.insert_text((X, y + size * 0.75), text, fontsize=size, fontname=font, color=(0, 0, 0))
        y += 13.4 if size >= 12 else (10.9 if size >= 9.5 else 10.4)


def replace_salesman(page: fitz.Page) -> None:
    for rect in page.search_for("Akshay Nalawade"):
        pad = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
        page.add_redact_annot(pad, fill=(1, 1, 1))
    page.apply_redactions()
    page.insert_text((500.82, 96), "shahabaj pathan", fontsize=9.5, fontname="helv", color=(0, 0, 0))


def restore_header_fields(page: fitz.Page) -> None:
    """Re-draw fields that can get clipped when replacing salesman name."""
    if not page.search_for("Credit"):
        page.insert_text((551.51, 86), "Credit", fontsize=9.5, fontname="helv", color=(0, 0, 0))
    if not page.search_for("25-07-2026"):
        page.insert_text((528.27, 104), "25-07-2026", fontsize=9.5, fontname="helv", color=(0, 0, 0))


def ensure_labels(page: fitz.Page) -> None:
    page.insert_text((X, 174), "Buyer", fontsize=8, fontname="helv", color=(0, 0, 0))
    page.insert_text((X, 307), "Shipped To", fontsize=8, fontname="helv", color=(0, 0, 0))


def edit_page(page: fitz.Page) -> None:
    redact_left_column_strings(page, OLD_BUYER)
    write_block(page, BUYER_LINES, start_y=177.1)

    redact_left_column_strings(page, OLD_SHIPPED)
    write_block(page, SHIPPED_LINES, start_y=309.8)

    replace_salesman(page)
    restore_header_fields(page)
    ensure_labels(page)


def main() -> None:
    doc = fitz.open(SRC)
    for i in range(doc.page_count):
        edit_page(doc[i])
    doc.save(OUT, garbage=4, deflate=True)
    doc.close()
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
