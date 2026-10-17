from io import BytesIO

import pytest
from PIL import Image

from src.receipt_scanner import (
    MAX_IMAGE_BYTES, ReceiptError, extract_receipt, suggest_category,
)


def test_rejects_empty_and_oversized_files():
    with pytest.raises(ReceiptError, match="empty"):
        extract_receipt(b"")
    with pytest.raises(ReceiptError, match="5 MB"):
        extract_receipt(b"x" * (MAX_IMAGE_BYTES + 1))


def test_rejects_invalid_image_content():
    with pytest.raises(ReceiptError, match="readable image"):
        extract_receipt(b"not an image")


def test_rejects_unsupported_image_format_before_ocr():
    output = BytesIO()
    Image.new("RGB", (2, 2)).save(output, format="GIF")
    with pytest.raises(ReceiptError, match="JPG"):
        extract_receipt(output.getvalue())


def test_receipt_category_suggestions_are_cautious():
    assert suggest_category("FRESH SUPERMARKET") == "Groceries"
    assert suggest_category("METRO TICKET") == "Transport"
    assert suggest_category("Receipt total: 50.00") == "Other"
