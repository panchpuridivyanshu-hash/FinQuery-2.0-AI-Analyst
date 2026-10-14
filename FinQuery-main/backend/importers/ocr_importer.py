import pytesseract
from PIL import Image
from datetime import datetime
from pytesseract import TesseractNotFoundError


def read_image_file(file_path):
    image = Image.open(file_path)

    try:
        text = pytesseract.image_to_string(image)
    except TesseractNotFoundError as error:
        raise ValueError(
            "OCR is not installed. Install Tesseract OCR, restart the backend, then scan the bill again."
        ) from error

    return text

import re


def parse_image_transactions(text):
    transactions = []

    date_matches = list(
        re.finditer(
            r"Date\s*[:.]?\s*(\d{4}-\d{2}-\d{2})",
            text,
            re.IGNORECASE
        )
    )

    for index, match in enumerate(date_matches):

        start = match.start()

        if index + 1 < len(date_matches):
            end = date_matches[index + 1].start()
        else:
            end = len(text)

        block = text[start:end]

        description_match = re.search(
            r"Description\s*[:.]?\s*(.*?)(?=\n|Category|Amount|$)",
            block,
            re.IGNORECASE
        )

        category_match = re.search(
            r"Category\s*[:.]?\s*(.*?)(?=\n|Amount|$)",
            block,
            re.IGNORECASE
        )

        amount_match = re.search(
            r"Amount\s*[:.]?\s*([\d,]+(?:\.\d+)?)",
            block,
            re.IGNORECASE
        )

        if description_match and category_match and amount_match:

            transaction = {
                "date": match.group(1).strip(),
                "description": description_match.group(1).strip(),
                "category": category_match.group(1).strip(),
                "amount": amount_match.group(1).replace(",", "").strip()
            }

            transactions.append(transaction)

    if transactions:
        return transactions

    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    date_match = re.search(
        r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
        text,
    )
    if not date_match:
        raise ValueError("Could not find a transaction date in this bill image.")

    date_value = date_match.group(1).replace("/", "-")
    parsed_date = None
    for date_format in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%d-%m-%y", "%m-%d-%y"):
        try:
            parsed_date = datetime.strptime(date_value, date_format).date().isoformat()
            break
        except ValueError:
            continue
    if not parsed_date:
        raise ValueError("The date found in the bill image is not valid.")

    amount_match = re.search(
        r"(?:grand\s*total|net\s*total|amount\s*paid|total\s*amount|total)\D{0,20}(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)",
        text,
        re.IGNORECASE,
    )
    if not amount_match:
        raise ValueError("Could not find a total amount in this bill image.")

    description = next(
        (line for line in lines if not re.search(r"(invoice|bill|date|total|gst|tax|mobile|phone|cash|upi)", line, re.I)),
        "Scanned bill",
    )
    return [{
        "date": parsed_date,
        "description": description[:255],
        "category": "Uncategorized",
        "amount": amount_match.group(1).replace(",", ""),
    }]
