# Personal Expense Tracker - Web Version

This version converts the original console-based Expense Tracker into a Flask web application.

## Run locally

1. Create/activate a virtual environment (optional but recommended).
2. Install dependencies:
   pip install -r requirements.txt
3. Start the app:
   python app.py
4. Open:
   http://127.0.0.1:5000

Data is stored in expenses.csv.

## Main features

- Add expense
- View expenses
- Search by title, category, or ID
- Edit expense
- Delete expense
- Total spending
- Category-wise breakdown
- Automatic ID generation
- Blank date automatically uses today's date
- Strict DD-MM-YYYY validation
- CSV persistence

## Render start command

gunicorn app:app
