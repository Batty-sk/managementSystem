from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, id, username, passkey, access_pages):
        self.id = id
        self.username = username
        self.passkey = passkey
        self.access_pages = access_pages


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing = db.Column(db.String(100))
    room = db.Column(db.String(100))
    confirmation_code = db.Column(db.String(50), unique=True)
    guest_name = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50))
    source = db.Column(db.String(50))

class Airbnb_earnings(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # auto_increment
    date = db.Column(db.Date)  # Date
    arriving_by_date = db.Column(db.Date)  # Arriving_by_date
    type = db.Column(db.String(255))  # Type
    confirmation_code = db.Column(db.String(255))  # Confirmation_code
    booking_date = db.Column(db.Date)  # Booking_date
    start_date = db.Column(db.Date)  # Start_date
    end_date = db.Column(db.Date)  # End_date
    nights = db.Column(db.Integer)  # Nights
    guest = db.Column(db.String(255))  # Guest
    listing = db.Column(db.String(255))  # Listing
    details = db.Column(db.String(500))  # Details
    reference_code = db.Column(db.String(255))  # Reference_code
    currency = db.Column(db.String(10))  # Currency
    amount = db.Column(db.Float)  # Amount
    paid_out = db.Column(db.Float)  # Paid_out
    service_fee = db.Column(db.Float)  # Service_fee
    fast_pay_fee = db.Column(db.Float)  # Fast_pay_fee
    cleaning_fee = db.Column(db.Float)  # Cleaning_fee
    gross_earning = db.Column(db.Float)  # Gross_earning
    occupancy_taxes = db.Column(db.Float)  # Occupancy_taxes
    area_code = db.Column(db.String(10))  # Area_code
    source = db.Column(db.String(100))  # Source
    deepan_report = db.Column(db.Integer, default=0)  # Deepan_report


    def as_earnings_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'arriving_by_date': self.arriving_by_date,
            'type': self.type,
            'confirmation_code': self.confirmation_code,
            'booking_date': self.booking_date,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'nights': self.nights,
            'guest': self.guest,
            'listing': self.listing,
            'details': self.details,
            'reference_code': self.reference_code,
            'currency': self.currency,
            'amount': self.amount,
            'paid_out': self.paid_out,
            'service_fee': self.service_fee,
            'fast_pay_fee': self.fast_pay_fee,
            'cleaning_fee': self.cleaning_fee,
            'gross_earning': self.gross_earning,
            'occupancy_taxes': self.occupancy_taxes,
            'area_code': self.area_code,
            'source': self.source,
            'deepan_report': self.deepan_report
        }

# Define your model for Listings
class Listings(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    listing_name = db.Column(db.String(100), unique=True)
    room = db.Column(db.String(100))
    area_code = db.Column(db.String(50))
    platform = db.Column(db.String(200))
    platform_url = db.Column(db.String(500))
    platform_account = db.Column(db.String(100))
    minimum_price = db.Column(db.Float)
    maximum_price = db.Column(db.Float)
    bed_type = db.Column(db.Float)
    no_of_bed = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_date = db.Column(db.DateTime)
    updated_by = db.Column(db.String(100))



    def as_dict(self):
        return {
            'id': self.id,
            'listing_name': self.listing_name,
            'room': self.room,
            'area_code': self.area_code,
            'platform': self.platform,
            'platform_url': self.platform_url,
            'platform_account': self.platform_account,
            'minimum_price': self.minimum_price,
            'maximum_price': self.maximum_price,
            'bed_type': self.bed_type,
            'no_of_bed': self.no_of_bed,
            'created_date': self.created_date,
            'created_by': self.created_by,
            'updated_date': self.updated_date,
            'updated_by': self.updated_by
        }
