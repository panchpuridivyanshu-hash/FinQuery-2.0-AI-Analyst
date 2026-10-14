from collections import defaultdict
from datetime import date


def _number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _month_key(value):
    try:
        return date.fromisoformat(str(value)[:10]).strftime("%Y-%m")
    except (TypeError, ValueError):
        return None


def _money(value):
    return f"₹{value:,.2f}"


def answer_query(question, transactions, today=None):
    """Answer common finance questions and return optional Chart.js-ready data."""
    text = " ".join(str(question).lower().split())
    today = today or date.today()
    selected = list(transactions)

    if any(term in text for term in (
        "last month", "previous month", "pichle mahine", "pichhle mahine", "पिछले महीने"
    )):
        month = 1 if today.month == 1 else today.month - 1
        year = today.year - 1 if today.month == 1 else today.year
        selected = [t for t in selected if _month_key(t.get("date")) == f"{year:04d}-{month:02d}"]
        period_label = "last month"
    elif any(term in text for term in (
        "this month", "current month", "is mahine", "iss mahine", "इस महीने"
    )):
        selected = [t for t in selected if _month_key(t.get("date")) == today.strftime("%Y-%m")]
        period_label = "this month"
    else:
        period_label = "all recorded transactions"

    total = sum(_number(t.get("amount")) for t in selected)
    category_totals = defaultdict(float)
    monthly_totals = defaultdict(float)
    for transaction in selected:
        category_totals[str(transaction.get("category") or "Other")] += _number(transaction.get("amount"))
        month = _month_key(transaction.get("date"))
        if month:
            monthly_totals[month] += _number(transaction.get("amount"))

    if not selected:
        return {"answer": f"There are no transactions for {period_label}.", "chart": None}

    chart_requested = any(term in text for term in (
        "chart", "graph", "plot", "ग्राफ", "चार्ट"
    ))
    monthly_requested = any(term in text for term in (
        "month", "monthly", "trend", "time", "mahine", "महीने", "मासिक"
    ))
    if chart_requested:
        chart_type = "pie" if any(term in text for term in ("pie", "donut", "circle", "पाई")) else (
            "line" if monthly_requested and any(term in text for term in ("line", "trend", "लाइन")) else "bar"
        )
        if monthly_requested:
            labels = sorted(monthly_totals)[-12:]
            values = [round(monthly_totals[label], 2) for label in labels]
            series_label = "Monthly spending"
            answer = f"Here is your monthly spending chart for {period_label}."
        else:
            ordered = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
            labels = [item[0] for item in ordered]
            values = [round(item[1], 2) for item in ordered]
            series_label = "Spending by category"
            answer = f"Here is your category-wise spending chart for {period_label}."
        return {
            "answer": answer,
            "chart": {"type": chart_type, "labels": labels, "values": values, "label": series_label},
        }

    count_requested = any(term in text for term in ("how many", "count", "number of", "kitne", "कितने"))
    average_requested = any(term in text for term in ("average", "avg", "औसत"))
    highest_transaction_requested = any(term in text for term in ("largest transaction", "highest transaction", "biggest expense"))

    if highest_transaction_requested:
        highest = max(selected, key=lambda item: _number(item.get("amount")))
        answer = f"Your largest transaction was {_money(_number(highest.get('amount')))} at {highest.get('description', 'Unknown')} on {highest.get('date', 'an unknown date')}."
    elif average_requested:
        answer = f"Your average transaction for {period_label} is {_money(total / len(selected))}."
    elif count_requested or "transaction" in text or "transactions" in text:
        answer = f"You have {len(selected)} transactions in {period_label}."
    else:
        matching_category = next(
            (category for category in sorted(category_totals, key=len, reverse=True) if category.lower() in text),
            None,
        )
        if matching_category:
            amount = category_totals[matching_category]
            answer = f"You spent {_money(amount)} in {matching_category} for {period_label}."
        elif any(term in text for term in ("category", "highest", "top", "most", "sabse zyada", "सबसे ज्यादा")):
            category, amount = max(category_totals.items(), key=lambda item: item[1])
            answer = f"Your highest-spending category for {period_label} is {category} at {_money(amount)}."
        elif any(term in text for term in ("total", "spend", "spending", "expense", "kharcha", "खर्च", "कुल")):
            answer = f"Your total spending for {period_label} is {_money(total)} across {len(selected)} transactions."
        else:
            answer = "I can answer questions about total spending, category spending, transaction count, averages, largest transactions, or make category and monthly charts."

    return {"answer": answer, "chart": None}
