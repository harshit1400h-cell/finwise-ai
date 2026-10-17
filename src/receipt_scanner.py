"""Local receipt OCR and conservative field extraction."""

from datetime import date
from io import BytesIO
import re
from typing import Any

from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG"}


class ReceiptError(ValueError):
    """Invalid receipt or OCR processing error safe to show to users."""


def suggest_category(text: str) -> str:
    normalized = text.casefold()
    keywords = {
        "Food": ("restaurant", "cafe", "coffee", "food", "pizza", "bakery"),
        "Groceries": ("grocery", "supermarket", "mart", "vegetable", "market"),
        "Transport": ("taxi", "uber", "ola", "fuel", "petrol", "metro", "bus"),
        "Education": ("school", "college", "bookstore", "tuition", "course"),
        "Shopping": ("retail", "clothing", "fashion", "mall", "electronics"),
        "Rent": ("rent", "landlord"),
        "Utilities": ("electricity", "water bill", "internet", "utility"),
        "Healthcare": ("pharmacy", "medical", "hospital", "clinic", "health"),
        "Entertainment": ("cinema", "movie", "theatre", "streaming"),
        "Travel": ("hotel", "flight", "airlines", "booking", "resort"),
    }
    for category, terms in keywords.items():
        if any(term in normalized for term in terms):
            return category
    return "Other"


def extract_receipt(uploaded: bytes) -> dict[str, Any]:
    if not uploaded:
        raise ReceiptError("The uploaded image is empty.")
    if len(uploaded) > MAX_IMAGE_BYTES:
        raise ReceiptError("Receipt images must be 5 MB or smaller.")
    try:
        image = Image.open(BytesIO(uploaded))
        image.verify()
        image = Image.open(BytesIO(uploaded))
        if image.format not in ALLOWED_FORMATS:
            raise ReceiptError("Upload a JPG, JPEG, or PNG image.")
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise ReceiptError("The file is not a readable image.") from None

    try:
        import pytesseract

        text = pytesseract.image_to_string(image)
    except Exception as exc:
        raise ReceiptError(
            "Receipt OCR is unavailable. Install the Tesseract OCR application and "
            "the pytesseract package, then try again."
        ) from exc
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    date_match = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    receipt_date = None
    if date_match:
        try:
            receipt_date = date(int(date_match.group(1)), int(date_match.group(2)),
                                int(date_match.group(3))).isoformat()
        except ValueError:
            receipt_date = None
    labeled_totals = []
    for match in re.finditer(
        r"(?:grand\s+total|amount\s+due|total)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*"
        r"(\d{1,7}(?:,\d{3})*(?:\.\d{1,2})?)",
        text, re.IGNORECASE,
    ):
        value = float(match.group(1).replace(",", ""))
        if value > 0:
            labeled_totals.append(value)
    all_amounts = [
        float(match.group(1).replace(",", ""))
        for match in re.finditer(r"(?:₹|Rs\.?|INR)\s*(\d{1,7}(?:,\d{3})*(?:\.\d{1,2})?)",
                                 text, re.IGNORECASE)
    ]
    possible_totals = labeled_totals or all_amounts
    likely_total = possible_totals[0] if len(possible_totals) == 1 else None
    return {
        "merchant": lines[0][:100] if lines else "",
        "date": receipt_date or date.today().isoformat(),
        "amount": likely_total,
        "category": suggest_category(text),
        "description": "Receipt purchase",
        "line_items": [line for line in lines if re.search(r"\d", line)],
        "extracted_text": text[:4000],
        "amount_needs_review": likely_total is None,
    }
