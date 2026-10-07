import csv
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

DATA_FILE = "expenses.csv"
DATE_FORMAT = "%d-%m-%Y"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "expense-tracker-demo-key")


# ---------------------------------------------------------------------
# MODEL CLASS - kept from the original console project
# ---------------------------------------------------------------------
class Expense:
    """Blueprint for a single expense record."""

    def __init__(self, expense_id, title, amount, category, date):
        self.id = expense_id
        self.title = title
        self.amount = amount
        self.category = category
        self.date = date

    def to_row(self):
        return [self.id, self.title, f"{self.amount:.2f}", self.category, self.date]

    @staticmethod
    def from_row(row):
        return Expense(
            expense_id=int(row[0]),
            title=row[1],
            amount=float(row[2]),
            category=row[3],
            date=row[4],
        )

    def __str__(self):
        return (
            f"{self.id:<5}{self.title:<25}{self.amount:>10.2f}   "
            f"{self.category:<15}{self.date}"
        )


# ---------------------------------------------------------------------
# MANAGER CLASS - kept from the original console project
# ---------------------------------------------------------------------
class ExpenseTracker:
    """Holds all expenses in memory and controls CRUD logic."""

    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.expenses = []
        self.next_id = 101
        self.load_from_disk()

    def load_from_disk(self):
        if not os.path.exists(self.filename):
            return

        try:
            with open(self.filename, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if not row:
                        continue
                    try:
                        expense = Expense.from_row(row)
                        self.expenses.append(expense)
                    except (ValueError, IndexError):
                        continue

            if self.expenses:
                self.next_id = max(e.id for e in self.expenses) + 1
        except OSError:
            pass

    def save_to_disk(self):
        try:
            with open(self.filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Title", "Amount", "Category", "Date"])
                for expense in self.expenses:
                    writer.writerow(expense.to_row())
            return True
        except OSError:
            return False

    def generate_id(self):
        new_id = self.next_id
        self.next_id += 1
        return new_id

    def find_by_id(self, expense_id):
        for expense in self.expenses:
            if expense.id == expense_id:
                return expense
        return None

    def add_expense(self, title, amount, category, date):
        expense = Expense(self.generate_id(), title, amount, category, date)
        self.expenses.append(expense)
        return expense

    def delete_expense(self, expense_id):
        expense = self.find_by_id(expense_id)
        if expense:
            self.expenses.remove(expense)
            return True
        return False

    def update_expense(self, expense_id, title=None, amount=None, category=None, date=None):
        expense = self.find_by_id(expense_id)
        if not expense:
            return None

        if title is not None:
            expense.title = title
        if amount is not None:
            expense.amount = amount
        if category is not None:
            expense.category = category
        if date is not None:
            expense.date = date

        return expense

    def get_grand_total(self):
        return sum(e.amount for e in self.expenses)

    def get_category_breakdown(self):
        breakdown = {}
        for e in self.expenses:
            breakdown[e.category] = breakdown.get(e.category, 0) + e.amount
        return breakdown


tracker = ExpenseTracker()


# ---------------------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------------------
def validate_date(raw_date):
    raw_date = raw_date.strip()

    if raw_date == "":
        return datetime.now().strftime(DATE_FORMAT)

    try:
        parsed = datetime.strptime(raw_date, DATE_FORMAT)
        # Enforce exact DD-MM-YYYY formatting.
        if parsed.strftime(DATE_FORMAT) != raw_date:
            return None
        return raw_date
    except ValueError:
        return None


# ---------------------------------------------------------------------
# WEB ROUTES
# ---------------------------------------------------------------------
@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    if search:
        expenses = [
            e for e in tracker.expenses
            if search.lower() in e.title.lower()
            or search.lower() in e.category.lower()
            or search == str(e.id)
        ]
    else:
        expenses = tracker.expenses

    return render_template(
        "index.html",
        expenses=expenses,
        total=tracker.get_grand_total(),
        breakdown=tracker.get_category_breakdown(),
        search=search,
        tracker_count=len(tracker.expenses),
    )


@app.route("/add", methods=["POST"])
def add_expense():
    title = request.form.get("title", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_raw = request.form.get("date", "").strip()

    if not title or not category:
        flash("Title and category cannot be empty.", "error")
        return redirect(url_for("index"))

    try:
        amount = float(amount_raw)
        if amount < 0:
            raise ValueError
    except ValueError:
        flash("Please enter a valid non-negative amount.", "error")
        return redirect(url_for("index"))

    date = validate_date(date_raw)
    if date is None:
        flash("Invalid date. Use the strict DD-MM-YYYY format.", "error")
        return redirect(url_for("index"))

    expense = tracker.add_expense(title, amount, category, date)

    if tracker.save_to_disk():
        flash(f"Expense added successfully. Generated ID: {expense.id}", "success")
    else:
        flash("Expense added in memory, but the CSV file could not be saved.", "error")

    return redirect(url_for("index"))


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    expense = tracker.find_by_id(expense_id)

    if not expense:
        flash(f"No expense found with ID {expense_id}.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_raw = request.form.get("date", "").strip()

        if not title or not category:
            flash("Title and category cannot be empty.", "error")
            return redirect(url_for("edit_expense", expense_id=expense_id))

        try:
            amount = float(amount_raw)
            if amount < 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid non-negative amount.", "error")
            return redirect(url_for("edit_expense", expense_id=expense_id))

        date = validate_date(date_raw)
        if date is None:
            flash("Invalid date. Use DD-MM-YYYY.", "error")
            return redirect(url_for("edit_expense", expense_id=expense_id))

        tracker.update_expense(
            expense_id,
            title=title,
            amount=amount,
            category=category,
            date=date,
        )
        tracker.save_to_disk()
        flash("Expense updated successfully.", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", expense=expense)


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if tracker.delete_expense(expense_id):
        if tracker.save_to_disk():
            flash(f"Expense {expense_id} deleted successfully.", "success")
        else:
            flash("Expense deleted in memory, but the CSV file could not be saved.", "error")
    else:
        flash(f"No expense found with ID {expense_id}.", "error")

    return redirect(url_for("index"))


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    return redirect(url_for("index", search=query))


@app.route("/summary")
def summary():
    return render_template(
        "summary.html",
        total=tracker.get_grand_total(),
        count=len(tracker.expenses),
        breakdown=tracker.get_category_breakdown(),
    )


if __name__ == "__main__":
    app.run(debug=True)
