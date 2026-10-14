from database.db import get_connection
import hmac
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date


def get_total_spending(user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result[0] or 0


def get_spending_by_category(user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = %s
        GROUP BY category
        ORDER BY total DESC
    """, (user_id,))

    results = cursor.fetchall()

    cursor.close()
    db.close()

    return results

def get_highest_spending_category(user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = %s
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """, (user_id,))

    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result


def get_average_transaction(user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT AVG(amount)
        FROM transactions
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result[0] or 0

def get_all_transactions(user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, date, description, category, amount
        FROM transactions
        WHERE user_id = %s
    """, (user_id,))

    transactions = cursor.fetchall()

    cursor.close()
    db.close()

    return transactions

def add_transaction(date, description, category, amount, user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (date, description, category, amount, user_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (date, description, category, amount, user_id))

    db.commit()

    cursor.close()
    db.close()

def delete_transaction(transaction_id, user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM transactions WHERE id = %s AND user_id = %s",
        (transaction_id, user_id)
    )
    changed = cursor.rowcount > 0

    db.commit()

    cursor.close()
    db.close()

    return changed

def update_transaction(transaction_id, date, description, category, amount, user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE transactions
        SET date = %s,
            description = %s,
            category = %s,
            amount = %s
        WHERE id = %s AND user_id = %s
    """, (date, description, category, amount, transaction_id, user_id))
    changed = cursor.rowcount > 0
    if not changed:
        cursor.execute(
            "SELECT 1 FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        changed = cursor.fetchone() is not None

    db.commit()

    cursor.close()
    db.close()

    return changed

def search_transactions(keyword, user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, date, description, category, amount
        FROM transactions
        WHERE user_id = %s
          AND (description LIKE %s OR category LIKE %s)
        ORDER BY date ASC
    """, (user_id, f"%{keyword}%", f"%{keyword}%"))

    results = cursor.fetchall()

    cursor.close()
    db.close()

    return results

def get_spending_by_date_range(start_date, end_date, user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE date BETWEEN %s AND %s AND user_id = %s
    """, (start_date, end_date, user_id))

    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result[0]

def get_monthly_spending(user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT YEAR(date) AS year,
               MONTH(date) AS month,
               SUM(amount) AS total
        FROM transactions
        WHERE user_id = %s
        GROUP BY YEAR(date), MONTH(date)
        ORDER BY year ASC, month ASC
    """, (user_id,))

    results = cursor.fetchall()

    cursor.close()
    db.close()

    return results

def register_user(name, email, password):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO users (name, email, password)
        VALUES (%s, %s, %s)
    """, (name, email, generate_password_hash(password)))

    db.commit()

    cursor.close()
    db.close()

    return True

def login_user(email, password):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, name, email, password
        FROM users
        WHERE email = %s
    """, (email,))

    user = cursor.fetchone()

    if user:
        stored_password = user[3]
        try:
            password_matches = check_password_hash(stored_password, password)
        except (ValueError, TypeError):
            # Upgrade accounts created before password hashing was added.
            password_matches = hmac.compare_digest(str(stored_password), password)

        if password_matches:
            if not str(stored_password).startswith(("scrypt:", "pbkdf2:")):
                cursor.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (generate_password_hash(password), user[0])
                )
                db.commit()
            user = user[:3]
        else:
            user = None

    cursor.close()
    db.close()

    return user

def get_total_transactions(user_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = %s
    """, (user_id,))

    total_transactions = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return total_transactions


def get_sidebar_summary(user_id, today=None, monthly_budget=15000):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute(
        "SELECT MAX(date) FROM transactions WHERE user_id = %s",
        (user_id,),
    )
    latest_transaction_date = cursor.fetchone()[0]
    today = today or latest_transaction_date or date.today()
    month_start = today.replace(day=1)
    if month_start.month == 1:
        previous_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        previous_start = month_start.replace(month=month_start.month - 1)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE user_id = %s AND date >= %s AND date < %s
        GROUP BY category
    """, (user_id, month_start, next_month_start))
    current_categories = cursor.fetchall()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE user_id = %s AND date >= %s AND date < %s
        GROUP BY category
    """, (user_id, previous_start, month_start))
    previous_categories = cursor.fetchall()
    cursor.close()
    db.close()

    current_totals = {str(category or "Other"): float(amount or 0) for category, amount in current_categories}
    previous_totals = {str(category or "Other"): float(amount or 0) for category, amount in previous_categories}
    spent = sum(current_totals.values())
    used_percent = (spent / monthly_budget * 100) if monthly_budget > 0 else 0

    if not current_totals or spent == 0:
        insight = "No spending recorded this month yet. Add a transaction to see your budget usage and insights."
    elif spent > monthly_budget:
        insight = f"You are {_money_for_summary(spent - monthly_budget)} over your monthly budget."
    elif used_percent >= 80:
        insight = f"You have used {used_percent:.0f}% of your monthly budget."
    else:
        category, amount = max(current_totals.items(), key=lambda item: item[1])
        previous_amount = previous_totals.get(category, 0)
        if previous_amount > 0:
            change = (amount - previous_amount) / previous_amount * 100
            direction = "up" if change >= 0 else "down"
            insight = f"{category} spending is {direction} {abs(change):.0f}% compared with last month."
        else:
            insight = f"Your highest spending category is {category} at {_money_for_summary(amount)} this month."

    return {
        "spent": round(spent, 2),
        "budget": monthly_budget,
        "percent_used": round(used_percent, 1),
        "progress_percent": min(max(round(used_percent, 1), 0), 100),
        "insight": insight,
        "period_label": today.strftime("%B %Y"),
    }


def _money_for_summary(value):
    return f"₹{value:,.0f}"

def import_transactions(transactions, user_id):
    db = get_connection()
    cursor = db.cursor()

    for transaction in transactions:
        cursor.execute("""
            INSERT INTO transactions
            (date, description, category, amount, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            transaction["date"],
            transaction["description"],
            transaction["category"],
            transaction["amount"],
            user_id
        ))

    db.commit()

    cursor.close()
    db.close()
