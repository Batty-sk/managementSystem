import pandas as pd
from sqlalchemy import text
  # Import app and db
from models import Reservation  # Import your models

bookings_df = pd.DataFrame()

def parse_date(date_str):
    formats = [
        '%m/%d/%Y',  # mm/dd/yyyy
        '%m-%d-%Y',  # mm-dd-yyyy
        # Add more formats as needed
    ]
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None  # Return None if no formats match

# Fetch area_code for the listing
def get_area_code(db,listing_name):
    if pd.isna(listing_name):  # Check if listing_name is NaN
        return None  # Return None or a default value if it is NaN
    query = text("SELECT area_code FROM listings WHERE listing_name = :listing_name")
    result = db.session.execute(query, {'listing_name': listing_name}).fetchone()
    return result[0] if result else None

def test_db_connection(app,db):
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Database connection successful.")
        except Exception as e:
            print("Database connection failed:", e)

def camelcase(s):
    """Convert a string to camel case."""
    return ''.join(word.capitalize() for word in s.split())

def refresh_bookings_df(app,db):
    global bookings_df
    with app.app_context():
        with db.engine.connect() as connection:
            result = connection.execute(db.session.query(Reservation).statement)
            columns = result.keys()
            data = result.fetchall()
            bookings_df = pd.DataFrame(data, columns=columns)
            bookings_df.columns = bookings_df.columns.str.strip().str.lower().str.replace(' ', '_')
            print(bookings_df)
            print("Columns in bookings_df:", bookings_df.columns)
            bookings_df['start_date'] = pd.to_datetime(bookings_df['start_date'])
            bookings_df['end_date'] = pd.to_datetime(bookings_df['end_date'])