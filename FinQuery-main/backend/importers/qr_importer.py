import cv2
from datetime import date
from urllib.parse import parse_qs, unquote, urlparse


def read_qr_code(file_path):
    image = cv2.imread(file_path)

    detector = cv2.QRCodeDetector()

    data, points, _ = detector.detectAndDecode(image)

    if not data:
        raise ValueError("No QR code found in image")

    return data

import re


def parse_qr_transaction(data):
    if data.lower().startswith("upi://"):
        query = parse_qs(urlparse(data).query)
        amount = query.get("am", [""])[0].strip()
        payee = unquote(query.get("pn", [""])[0]).strip()
        note = unquote(query.get("tn", [""])[0]).strip()

        if not amount:
            raise ValueError(
                "This UPI QR code does not contain an amount. Enter the transaction manually after payment."
            )

        return {
            "date": date.today().isoformat(),
            "description": note or payee or "UPI payment",
            "category": "UPI Payment",
            "amount": amount.replace(",", ""),
        }

    date_match = re.search(
        r"Date\s*[:.]?\s*(\d{4}-\d{2}-\d{2})",
        data,
        re.IGNORECASE
    )

    description_match = re.search(
        r"Description\s*[:.]?\s*(.*?)(?=\n|Category|Amount|$)",
        data,
        re.IGNORECASE
    )

    category_match = re.search(
        r"Category\s*[:.]?\s*(.*?)(?=\n|Amount|$)",
        data,
        re.IGNORECASE
    )

    amount_match = re.search(
        r"Amount\s*[:.]?\s*([\d,]+(?:\.\d+)?)",
        data,
        re.IGNORECASE
    )

    if not date_match:
        raise ValueError("QR data is missing date")

    if not description_match:
        raise ValueError("QR data is missing description")

    if not category_match:
        raise ValueError("QR data is missing category")

    if not amount_match:
        raise ValueError("QR data is missing amount")

    transaction = {
        "date": date_match.group(1).strip(),
        "description": description_match.group(1).strip(),
        "category": category_match.group(1).strip(),
        "amount": amount_match.group(1).replace(",", "").strip()
    }

    return transaction
