import os
import tempfile
from pathlib import Path
from functools import wraps
from secrets import token_hex

from services.import_preview import create_preview
from services.import_history import save_import_history
from services.query_assistant import answer_query
from datetime import date
from flask import Flask, redirect, request, session, url_for
from flask_cors import CORS
from mysql.connector.errors import Error as MySQLError, IntegrityError
from importers.pdf_importer import read_pdf_file, parse_pdf_transactions
from importers.docx_importer import read_docx_file, parse_docx_transactions
from importers.ocr_importer import read_image_file, parse_image_transactions
from importers.csv_importer import read_csv_file
from importers.ocr_importer import read_image_file
from importers.qr_importer import read_qr_code, parse_qr_transaction
from services.analysis import import_transactions
from services.data_normalizer import normalize_transaction
from services.import_validator import validate_transactions
from services.analysis import (
    get_total_spending,
    get_spending_by_category,
    get_highest_spending_category,
    get_average_transaction,
    get_all_transactions,
    add_transaction,
    delete_transaction,
    register_user,
    update_transaction,
    search_transactions,
    get_spending_by_date_range,
    get_monthly_spending,
    login_user,
    get_total_transactions,
    get_sidebar_summary
)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path="/frontend",
)
app.secret_key = os.getenv("FINQUERY_SECRET_KEY") or token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FINQUERY_HTTPS", "false").lower() == "true",
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
)


@app.after_request
def prevent_frontend_cache(response):
    if request.path.startswith("/frontend/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.errorhandler(MySQLError)
def handle_database_error(error):
    app.logger.exception("Database request failed: %s", error)
    return {
        "success": False,
        "message": "Database connection failed. Check MySQL and restart the backend.",
    }, 503


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return {"success": False, "message": "Please login first"}, 401
        return view(*args, **kwargs)
    return wrapped


def save_imported_transactions(transactions, user_id, file_type):
    if not transactions:
        raise ValueError("No transactions were found. Use a file with transaction details or a readable bill image.")

    validated = validate_transactions(transactions)
    if validated["errors"]:
        first_error = validated["errors"][0]
        raise ValueError(f"Transaction row {first_error['row']}: {', '.join(first_error['errors'])}")

    normalized = [normalize_transaction(transaction) for transaction in validated["valid_transactions"]]
    import_transactions(normalized, user_id)
    save_import_history(user_id, file_type, len(normalized))
    return normalized

@app.route("/api/import/preview", methods=["POST"])
def import_preview():
    if "user_id" not in session:
        return {
            "success": False,
            "message": "Please login first"
        }, 401

    data = request.get_json()

    if not data or "transactions" not in data:
        return {
            "success": False,
            "message": "No transactions provided"
        }, 400

    preview = create_preview(data["transactions"])

    return {
        "success": True,
        "preview": preview
    }

@app.route("/api/import/history")
def import_history():
    if "user_id" not in session:
        return {
            "success": False,
            "message": "Please login first"
        }, 401

    from database.db import get_connection

    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, file_type, record_count, imported_at
        FROM import_history
        WHERE user_id = %s
        ORDER BY imported_at DESC
    """, (session["user_id"],))

    results = cursor.fetchall()

    cursor.close()
    db.close()

    history = []

    for row in results:
        history.append({
            "id": row[0],
            "file_type": row[1],
            "record_count": row[2],
            "imported_at": str(row[3])
        })

    return {
        "success": True,
        "history": history
    }

@app.route("/api/import/csv", methods=["POST"])
def import_csv():
    if "user_id" not in session:
        return {"success": False, "message": "Please login first"}, 401

    if "file" not in request.files:
        return {"success": False, "message": "No file uploaded"}, 400

    file = request.files["file"]

    if file.filename == "":
        return {"success": False, "message": "No file selected"}, 400

    if not file.filename.lower().endswith(".csv"):
        return {"success": False, "message": "Only CSV files are allowed"}, 400

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".csv"
    )

    file_path = temp_file.name

    temp_file.close()

    try:
        file.save(file_path)
        transactions = read_csv_file(file_path)

        transactions = save_imported_transactions(transactions, session["user_id"], "csv")

        return {
            "success": True,
            "message": "CSV transactions imported successfully!",
            "count": len(transactions)
        }

    except ValueError as error:

        return {
            "success": False,
            "message": str(error)
        }, 400

    finally:

        if os.path.exists(file_path):
            os.remove(file_path)

@app.route("/api/import/pdf", methods=["POST"])
def import_pdf():
    if "user_id" not in session:
        return {"success": False, "message": "Please login first"}, 401

    if "file" not in request.files:
        return {"success": False, "message": "No file uploaded"}, 400

    file = request.files["file"]

    if file.filename == "":
        return {"success": False, "message": "No file selected"}, 400

    if not file.filename.lower().endswith(".pdf"):
        return {"success": False, "message": "Only PDF files are allowed"}, 400

    if not file.filename.lower().endswith(".pdf"):
        return {"success": False, "message": "Only PDF files are allowed"}, 400

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    file_path = temp_file.name
    temp_file.close()

    try:
        file.save(file_path)
        text = read_pdf_file(file_path)

        transactions = parse_pdf_transactions(text)

        transactions = save_imported_transactions(transactions, session["user_id"], "pdf")

        return {
            "success": True,
            "message": "PDF transactions imported successfully!",
            "count": len(transactions),
            "transactions": transactions
        }

    except Exception as error:
        return {
            "success": False,
            "message": str(error)
        }, 400
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route("/api/import/docx", methods=["POST"])
def import_docx():

    if "user_id" not in session:
        return {
            "success": False,
            "message": "Please login first"
        }, 401

    if "file" not in request.files:
        return {
            "success": False,
            "message": "No file uploaded"
        }, 400

    file = request.files["file"]

    if file.filename == "":
        return {
            "success": False,
            "message": "No file selected"
        }, 400

    if not file.filename.lower().endswith(".docx"):
        return {
            "success": False,
            "message": "Only DOCX files are allowed"
        }, 400

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    file_path = temp_file.name
    temp_file.close()

    try:
        file.save(file_path)

        text = read_docx_file(file_path)

        transactions = parse_docx_transactions(text)

        transactions = save_imported_transactions(transactions, session["user_id"], "docx")

        return {
            "success": True,
            "message": "DOCX transactions imported successfully!",
            "count": len(transactions),
            "transactions": transactions
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }, 400
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route("/api/import/image", methods=["POST"])
def import_image():

    if "user_id" not in session:
        return {
            "success": False,
            "message": "Please login first"
        }, 401

    if "file" not in request.files:
        return {
            "success": False,
            "message": "No file uploaded"
        }, 400

    file = request.files["file"]

    if file.filename == "":
        return {
            "success": False,
            "message": "No file selected"
        }, 400

    allowed_extensions = [".png", ".jpg", ".jpeg"]

    if not any(
        file.filename.lower().endswith(ext)
        for ext in allowed_extensions
    ):
        return {
            "success": False,
            "message": "Only PNG, JPG and JPEG files are allowed"
        }, 400

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1].lower())
    file_path = temp_file.name
    temp_file.close()

    try:
        file.save(file_path)

        text = read_image_file(file_path)

        transactions = parse_image_transactions(text)

        transactions = save_imported_transactions(transactions, session["user_id"], "image")

        return {
            "success": True,
            "message": "Image transactions imported successfully!",
            "count": len(transactions),
            "transactions": transactions
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }, 400
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route("/api/import/qr", methods=["POST"])
def import_qr():

    if "user_id" not in session:
        return {
            "success": False,
            "message": "Please login first"
        }, 401

    if "file" not in request.files:
        return {
            "success": False,
            "message": "No file uploaded"
        }, 400

    file = request.files["file"]

    if file.filename == "":
        return {
            "success": False,
            "message": "No file selected"
        }, 400

    allowed_extensions = [".png", ".jpg", ".jpeg"]

    if not any(
        file.filename.lower().endswith(ext)
        for ext in allowed_extensions
    ):
        return {
            "success": False,
            "message": "Only PNG, JPG and JPEG files are allowed"
        }, 400

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1].lower())
    file_path = temp_file.name
    temp_file.close()

    try:
        file.save(file_path)

        data = read_qr_code(file_path)

        transaction = parse_qr_transaction(data)

        save_imported_transactions([transaction], session["user_id"], "qr")

        return {
            "success": True,
            "message": "QR transaction imported successfully!",
            "count": 1,
            "transaction": transaction
        }

    except ValueError as error:

        return {
            "success": False,
            "message": str(error)
        }, 400

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }, 400
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

CORS(
    app,
    supports_credentials=True,
    origins=["http://127.0.0.1:5500", "http://localhost:5500"]
)


@app.route("/")
def home():
    return redirect(url_for("static", filename="register.html"))


@app.route("/api/summary")
@login_required
def summary():
    user_id = session["user_id"]

    total = get_total_spending(user_id)
    total_transactions = get_total_transactions(user_id)
    categories = get_spending_by_category(user_id)
    highest = get_highest_spending_category(user_id)
    average = get_average_transaction(user_id)
    
    return {
        "total_spending": float(total),
        "total_transactions": total_transactions,
        "highest_category": highest[0] if highest else None,
        "highest_category_amount": float(highest[1]) if highest else 0,
        "average_transaction": float(average),
        "spending_by_category": [
            {
                "category": category,
                "amount": float(amount)
            }
            for category, amount in categories
        ]
    }
@app.route("/api/transactions")
@login_required
def transactions():
    user_id = session["user_id"]

    results = get_all_transactions(user_id)

    transaction_data = []

    for transaction in results:
        transaction_data.append({
            "id": transaction[0],
            "date": str(transaction[1]),
            "description": transaction[2],
            "category": transaction[3],
            "amount": float(transaction[4])
        })

    return {
        "transactions": transaction_data
    }

@app.route("/api/transactions", methods=["POST"])
@login_required
def create_transaction():
    data = request.get_json()
    if not isinstance(data, dict) or not all(
        field in data for field in ("date", "description", "category", "amount")
    ):
        return {"success": False, "message": "Invalid transaction data"}, 400

    date = data["date"]
    description = data["description"]
    category = data["category"]
    amount = data["amount"]

    user_id = session["user_id"]

    add_transaction(date, description, category, amount, user_id)

    return {
        "message": "Transaction added successfully!"
    }

@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
@login_required
def delete_transaction_api(transaction_id):
    if not delete_transaction(transaction_id, session["user_id"]):
        return {"success": False, "message": "Transaction not found"}, 404

    return {
        "message": "Transaction deleted successfully!"
    }

@app.route("/api/transactions/<int:transaction_id>", methods=["PUT"])
@login_required
def update_transaction_api(transaction_id):
    data = request.get_json()
    if not isinstance(data, dict) or not all(
        field in data for field in ("date", "description", "category", "amount")
    ):
        return {"success": False, "message": "Invalid transaction data"}, 400

    date = data["date"]
    description = data["description"]
    category = data["category"]
    amount = data["amount"]

    updated = update_transaction(
        transaction_id,
        date,
        description,
        category,
        amount,
        session["user_id"]
    )

    if not updated:
        return {"success": False, "message": "Transaction not found"}, 404

    return {
        "message": "Transaction updated successfully!"
    }

@app.route("/api/transactions/search")
@login_required
def search_transactions_api():
    keyword = request.args.get("keyword", "")

    results = search_transactions(keyword, session["user_id"])

    transaction_data = []

    for transaction in results:
        transaction_data.append({
            "id": transaction[0],
            "date": str(transaction[1]),
            "description": transaction[2],
            "category": transaction[3],
            "amount": float(transaction[4])
        })

    return {
        "transactions": transaction_data
    }

@app.route("/api/transactions/date-range")
@login_required
def date_range_analysis():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return {"success": False, "message": "start_date and end_date are required"}, 400

    total = get_spending_by_date_range(start_date, end_date, session["user_id"])

    if total is None:
        total = 0

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_spending": float(total)
    }

@app.route("/api/transactions/monthly")
@login_required
def monthly_spending():
    user_id = session["user_id"]

    results = get_monthly_spending(user_id)

    monthly_data = []

    for year, month, total in results:
        monthly_data.append({
            "year": year,
            "month": month,
            "total_spending": float(total)
        })

    return {
        "monthly_spending": monthly_data
    }


@app.route("/api/sidebar-summary")
@login_required
def sidebar_summary():
    return get_sidebar_summary(session["user_id"])


@app.route("/api/assistant/query", methods=["POST"])
@login_required
def assistant_query():
    data = request.get_json()
    question = data.get("question") if isinstance(data, dict) else None
    if not isinstance(question, str) or not question.strip():
        return {"success": False, "message": "Please enter a question"}, 400
    if len(question) > 500:
        return {"success": False, "message": "Question must be 500 characters or fewer"}, 400

    transactions = [
        {
            "date": str(row[1]),
            "description": row[2],
            "category": row[3],
            "amount": float(row[4]),
        }
        for row in get_all_transactions(session["user_id"])
    ]
    result = answer_query(question.strip(), transactions)
    return {"success": True, **result}

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not isinstance(data, dict) or not all(
        isinstance(data.get(k), str) and data[k].strip()
        for k in ("name", "email", "password")
    ):
        return {"success": False, "message": "Name, email and password are required"}, 400

    name = data["name"]
    email = data["email"]
    password = data["password"]

    try:
        register_user(name, email, password)
    except IntegrityError:
        return {"success": False, "message": "That email is already registered. Please log in instead."}, 409

    return {
        "success": True,
        "message": "User registered successfully!"
    }

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not isinstance(data, dict) or not all(
        isinstance(data.get(k), str) and data[k]
        for k in ("email", "password")
    ):
        return {"success": False, "message": "Email and password are required"}, 400

    email = data["email"]
    password = data["password"]

    user = login_user(email, password)

    if user:
        session.clear()
        session["user_id"] = user[0]

        return {
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user[0],
                "name": user[1],
                "email": user[2]
            }
        }

    return {
        "success": False,
        "message": "Invalid email or password"
    }, 401

@app.route("/api/me")
def current_user():
    if "user_id" not in session:
        return {
            "logged_in": False
        }, 401

    return {
        "logged_in": True,
        "user_id": session["user_id"]
    }


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
