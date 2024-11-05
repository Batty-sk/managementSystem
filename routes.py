from models import User,Listings,Reservation,Airbnb_earnings
from utils import camelcase, get_area_code, parse_date, refresh_bookings_df, test_db_connection,get_physical_rooms
from constants import room_colors,status_colors
import pandas as pd
from sqlalchemy import text
from datetime import datetime
from sqlalchemy import text  # Ensure this import is presen
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user


users = [
    User(id=72, username='consultant', passkey='123456', access_pages=['home', 'bookings', 'earnings']),
    User(id=7, username='deepan', passkey='449531', access_pages=['home', 'deepan_report']),  # New user added
    User(id=9, username='slawek', passkey='567434', access_pages=['home', 'calendar']),  # New user added
]


def register_routes(app,db):
    @app.route('/earnings', methods=['GET'])
    @login_required
    def get_earnings():
        global earnings  # Declare the global variable
        earnings = Airbnb_earnings.query.all()  # Update the global earnings variable
        if(current_user.username == 'deepan'):
            earnings = Airbnb_earnings.query.filter_by(deepan_report=1, area_code='EC').all()
        
        return jsonify([earning.as_earnings_dict() for earning in earnings]), 200


    # Update a earnings
    @app.route('/earnings/<int:earning_id>', methods=['PUT'])
    @login_required
    def update_earning(earning_id):
        data = request.json
        print(data)
        airbnb_earning = Airbnb_earnings.query.get_or_404(earning_id)
        airbnb_earning.deepan_report = data.get('deepan_report', airbnb_earning.deepan_report)
        airbnb_earning.area_code = data.get('area_code', airbnb_earning.area_code)
        db.session.commit()
        return jsonify({'message': 'Earning updated successfully'}), 200

    @app.route('/earnings/<int:earning_id>', methods=['GET'])
    @login_required
    def get_earnings_by_id(earning_id):
        earning = Airbnb_earnings.query.get_or_404(earning_id)
        return jsonify(earning.as_earnings_dict()), 200


    # New route to display the listings page
    @app.route('/earnings_page')
    @login_required
    def earnings_page():
        global earnings  # Declare the global variable
        get_earnings()
        print(earnings)
        return render_template('earnings.html', Earnings=earnings)



    bookings_df = pd.DataFrame()


    app.template_filter('camelcase')(camelcase)

    dropdown_options = ["Airbnb-Mark", "Airbnb-Stacy"]

    # Define status colors for checkin and checkout

    # Initialize physical_rooms from the database
    physical_rooms = get_physical_rooms(app,Listings)


    # Define a specific route for Deepan
    @app.route('/deepan_report')
    @login_required
    def deepan_report():
        if current_user.username != 'deepan':
            return 'Access denied', 403  # Forbidden access
        return render_template('earnings.html')  # Render Deepan's specific page

    # Update the login function to redirect users appropriately
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            data = request.get_json()  # Expecting JSON payload
            if not data:
                return jsonify({'success': False, 'message': 'No input data provided'}), 400
            
            username = data.get('username').strip()
            passkey = data.get('passkey')
            
            if not username or not passkey:
                return jsonify({'success': False, 'message': 'Username and passkey are required'}), 400
            
            for user in users:
                if user.username == username and user.passkey == passkey:
                    login_user(user)
                    # Determine the redirect URL based on the user
                    if user.username == 'deepan':
                        redirect_url = url_for('deepan_report')
                    # elif user.username == 'slawek':
                    #     redirect_url = url_for('calendar')
                    else:
                        redirect_url = url_for('home')
                    return jsonify({'success': True, 'redirect_url': redirect_url}), 200
            
            # If authentication fails
            return jsonify({'success': False, 'message': 'Invalid username or passkey'}), 401
        
        # For GET requests, render the login page
        return render_template('login.html', users=users)

    # Logout route
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    # Home route to display current bookings
    @app.route('/Bookings')
    @login_required
    def bookings():
        # refresh_bookings_df()
        # # print(bookings_df)
        # current_date = datetime.date.today()
        # unique_listings = bookings_df['listing_name'].dropna().unique().tolist()
        # bookings_records = bookings_df.to_dict(orient='records')
        return render_template(
            'bookings.html',
            # bookings=bookings_records,
            # unique_listings=unique_listings,
            # dropdown_options=dropdown_options,
            # current_date=current_date
        )

    @app.route('/')
    @login_required
    def home():
        if(current_user.username == 'deepan'):
            global earnings  # Declare the global variable
            get_earnings()
            return render_template('earnings.html')
        elif(current_user.username == 'slawek'):
            year = pd.Timestamp.now().year
            month = pd.Timestamp.now().month
            bookings_data = []
            print(bookings_df)
            for booking in bookings_df.itertuples():
                bookings_data.append({
                    'title': booking.guest_name,
                    'start': booking.start_date.strftime('%Y-%m-%d'),
                    'end': booking.end_date.strftime('%Y-%m-%d')
                })
            return render_template('calendar.html', bookings=bookings_data, room_colors=room_colors, status_colors=status_colors)
        return render_template('index.html')  # or whatever your home template is

    # Route to display calendar with bookings
    @app.route('/calendar')
    @login_required
    def show_calendar():
        year = pd.Timestamp.now().year
        month = pd.Timestamp.now().month
        bookings_data = []
        print(bookings_df)
        for booking in bookings_df.itertuples():
            bookings_data.append({
                'title': booking.guest_name,
                'start': booking.start_date.strftime('%Y-%m-%d'),
                'end': booking.end_date.strftime('%Y-%m-%d')
            })
        return render_template('calendar.html', bookings=bookings_data, room_colors=room_colors, status_colors=status_colors)

    # Modified Route to Get Bookings Summary Data as JSON
    @app.route('/api/bookings_summary')
    @login_required
    def get_bookings_summary():
        refresh_bookings_df(app=app,db=db)
        summary_dict = {}
        today = pd.Timestamp.now().normalize()
        
        # Initialize counters for AC and EC listings
        ac_count = 0
        ec_count = 0
        
        for _, booking in bookings_df.iterrows():
            checkin = booking['start_date']
            checkout = booking['end_date']
            status = booking['status']
            listing = booking['listing']  # Get the listing for the current booking
            date_range = pd.date_range(start=checkin, end=checkout)
            
            for single_date in date_range:
                if single_date < today:
                    continue
                date_str = single_date.strftime('%Y-%m-%d')
                if date_str not in summary_dict:
                    summary_dict[date_str] = {
                        'date': date_str,
                        'checkins': 0,
                        'currently_staying': 0,
                        'checkouts': 0,
                        "listing": listing
                    }
                if single_date == checkin and (status == "Confirmed" or status == "Currently hosting"):
                    summary_dict[date_str]['checkins'] += 1
                if status == "Currently hosting" and single_date not in [checkout]:
                    summary_dict[date_str]['currently_staying'] += 1
                if (booking['end_date'] == single_date and status == "Currently hosting") or status == "Checking out today":
                    summary_dict[date_str]['checkouts'] += 1
                
                # Check if the listing matches physical rooms
                for room_type, rooms in physical_rooms.items():
                    if listing in rooms.get('AC001', []):  # Adjust as needed for other room types
                        summary_dict[date_str]['ac_count'] += 1
                    elif listing in rooms.get('EC001', []):
                        summary_dict[date_str]['ec_count'] += 1

        summary_data = sorted(summary_dict.values(), key=lambda x: x['date'])
        print(physical_rooms)
        return jsonify(summary_data)

    # New route to get detailed bookings data as JSON (optional)
    @app.route('/api/bookings_detail')
    @login_required
    def get_bookings_detail():
        refresh_bookings_df()
        bookings_data = []
        today = pd.Timestamp.now().normalize()
        listings = Listings.query.all()  # Fetch all listings from the database
        for _, booking in bookings_df.iterrows():
            checkin = booking['start_date']
            checkout = booking['end_date']
            if booking['status'] in ["Confirmed", "Currently hosting", "Pending", "Past guest", "Review guest", "Checking out today"]:
                date_range = pd.date_range(start=checkin, end=checkout)
                print(date_range)
                for single_date in date_range:
                    if single_date < today:
                        status = "Stayed"
                    else:
                        status = "Currently hosting" if single_date not in [checkin, checkout] and booking['status'] == "Currently hosting" else booking['status'] 
                        status = "Checked In" if single_date == checkin else status
                        status = "Check Out" if single_date == checkout else status
                        status = "Confirmed" if (single_date == checkin and single_date in [today, today + pd.Timedelta(days=1)]) else status
                        status = "Checking out today" if booking['status'] == "Checking out today" else status
                        status = "Pending" if booking['status'] == "Pending" else status
                    
                    # Check if the booking listing_name matches the listings listing_name
                    # and append the area_code from the listings to the booking guest
                    guest_name = booking['guest_name']
                    for listing in listings:
                        if listing.listing_name == booking['listing']:
                            guest_name = f"{listing.area_code} {guest_name}"
                            break
                    
                    bookings_data.append({
                        'title': guest_name,  # Use the modified guest_name with area_code
                        'start': single_date.strftime('%Y-%m-%d'),
                        'end': single_date.strftime('%Y-%m-%d'),
                        'color': status_colors.get(status, 'gray'),
                        'status_type': status
                    })
        return jsonify(bookings_data)

    # New route to upload CSV reservation files
    @app.route('/upload_csv', methods=['POST'])
    @login_required
    def upload_csv():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            df['start_date'] = pd.to_datetime(df['start_date'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
            df['end_date'] = pd.to_datetime(df['end_date'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
            source = request.form.get('source')
            if source == "":
                source = request.form.get('listing_name')
            for _, row in df.iterrows():
                existing_reservation = Reservation.query.filter_by(confirmation_code=row['confirmation_code']).first()
                if existing_reservation:
                    existing_reservation.listing = row['listing']
                    existing_reservation.guest_name = row['guest_name']
                    existing_reservation.start_date = row['start_date']
                    existing_reservation.end_date = row['end_date']
                    existing_reservation.status = row['status']
                    existing_reservation.source = source
                else:
                    reservation = Reservation(
                        confirmation_code=row['confirmation_code'],
                        listing=row['listing'],
                        guest_name=row['guest_name'],
                        start_date=row['start_date'],
                        end_date=row['end_date'],
                        status=row['status'],
                        source=source
                    )
                    db.session.add(reservation)
            db.session.commit()
            return jsonify({'message': 'File uploaded and data inserted/updated successfully'}), 200
        return jsonify({'error': 'Invalid file format'}), 400

    # Test database connection

    # Call the test function after initializing the app
    test_db_connection(app=app,db=db)

    # New route to display the uploads page
    @app.route('/uploads')
    @login_required
    def uploads():
        return render_template('uploads.html', dropdown_options=dropdown_options)

    @app.route('/airbnbbookings', methods=['POST'])
    def webhook():
        payload = request.get_json()  # Parse the JSON payload
        print(payload)
        if payload:
            # Extract relevant information from the payload
            parsed_data = payload.get('payload', {}).get('parsed', {})
            guest_name = parsed_data.get('Guest Full Name', '')
            check_in_date = parsed_data.get('Booking Check In Date', '')
            check_in_time = parsed_data.get('Booking Check In Time', '')
            check_out_date = parsed_data.get('Booking Checkout Date', '')
            check_out_time = parsed_data.get('Booking Checkout Time', '')
            guest_count = parsed_data.get('Booking Guests No', '')
            listing_name = parsed_data.get('Listing Name', '')
            guest_paid_total = parsed_data.get('Guest Paid Total', '')
            host_payout_total = parsed_data.get('Host Payout Total', '')
            from_email = parsed_data.get('from', '')
            received_at_datetime = parsed_data.get('received_at_datetime', '')
            created_at = parsed_data.get('created_at', '')
            confirmation_code = parsed_data.get('confirmation_code', '')
            
            # Print or process the extracted data
            print(f"Guest Name: {guest_name}")
            print(f"Check In Date: {check_in_date}")
            print(f"Check Out Date: {check_out_date}")
            print(f"Confirmation Code: {confirmation_code}")
            print(f"Guest Count: {guest_count}")
            print(f"Listing Name: {listing_name}")
            print(f"Guest Paid Total: {guest_paid_total}")
            print(f"Host Payout Total: {host_payout_total}")
            print(f"From Email: {from_email}")
            print(f"Received At Datetime: {received_at_datetime}")
            print(f"Created At: {created_at}")

            # Extract date and time components
            current_year = datetime.now().year  # Get the current year
            check_in_date_obj = datetime.strptime(f"{current_year} {check_in_date}", '%Y %a, %b %d')
            check_out_date_obj = datetime.strptime(f"{current_year} {check_out_date}", '%Y %a, %b %d')
            check_in_time_obj = datetime.strptime(check_in_time, '%H:%M %p')
            check_out_time_obj = datetime.strptime(check_out_time, '%H:%M %p')

            # Format the extracted date and time components
            formatted_check_in_date = check_in_date_obj.strftime('%Y-%m-%d')
            formatted_check_out_date = check_out_date_obj.strftime('%Y-%m-%d')
            formatted_check_in_time = check_in_time_obj.strftime('%H:%M:%S')
            formatted_check_out_time = check_out_time_obj.strftime('%H:%M:%S')

            print(f"Formatted Check-In Date: {formatted_check_in_date}")
            print(f"Formatted Check-Out Date: {formatted_check_out_date}")
            print(f"Formatted Check-In Time: {formatted_check_in_time}")
            print(f"Formatted Check-Out Time: {formatted_check_out_time}")

            if from_email == "connect@Markkumar.co.uk":
                source = "Airbnb-Mark"
            elif from_email == "Stacy@Markkumar.co.uk":
                source = "Airbnb-Stacy"
            else:
                source = "Airbnb-Unknown"
            
            # Update existing reservation if it exists
            existing_reservation = Reservation.query.filter_by(confirmation_code=confirmation_code).first()
            if existing_reservation:
                existing_reservation.listing = listing_name
                existing_reservation.guest_name = guest_name
                existing_reservation.start_date = check_in_date
                existing_reservation.end_date = check_out_date
                existing_reservation.status = "Confirmed"
                existing_reservation.source = source
            else:
                reservation = Reservation(
                    confirmation_code=confirmation_code,
                    listing=listing_name,
                    guest_name=guest_name,
                    start_date=formatted_check_in_date,
                    end_date=formatted_check_out_date,
                    status="Confirmed",
                    source=source
                )
                db.session.add(reservation)
            db.session.commit()

            return jsonify(success=True)
        
        return jsonify(success=False, error="Invalid payload"), 400

    # New route to display the listings page
    @app.route('/listings_page')
    @login_required
    def listings_page():
        listings = Listings.query.all()
        return render_template('listings.html', listings=listings)

    # CRUD operations for Listings

    # Create a new listing
    @app.route('/listings', methods=['POST'])
    @login_required
    def create_listing():
        data = request.json
        new_listing = Listings(
            listing_name=data['listing_name'],
            room=data.get('room'),
            area_code=data.get('area_code'),
            platform=data.get('platform'),
            platform_url=data.get('platform_url'),
            platform_account=data.get('platform_account'),
            minimum_price=data.get('minimum_price'),
            maximum_price=data.get('maximum_price'),
            bed_type=data.get('bed_type'),
            no_of_bed=data.get('no_of_bed'),
            created_by=current_user.username
        )
        db.session.add(new_listing)
        db.session.commit()
        return jsonify({'message': 'Listing created successfully'}), 201

    # Read all listings
    @app.route('/listings', methods=['GET'])
    @login_required
    def get_listings():
        listings = Listings.query.all()
        return jsonify([listing.as_dict() for listing in listings]), 200

    # Read all listings
    @app.route('/listings/<int:listing_id>', methods=['GET'])
    @login_required
    def get_listings_by_id(listing_id):
        listing = Listings.query.get_or_404(listing_id)
        return jsonify(listing.as_dict()), 200

    # Update a listing
    @app.route('/listings/<int:listing_id>', methods=['PUT'])
    @login_required
    def update_listing(listing_id):
        data = request.json
        listing = Listings.query.get_or_404(listing_id)
        listing.listing_name = data.get('listing_name', listing.listing_name)
        listing.room = data.get('room', listing.room)
        listing.area_code = data.get('area_code', listing.area_code)
        listing.platform = data.get('platform', listing.platform)
        listing.platform_url = data.get('platform_url', listing.platform_url)
        listing.platform_account = data.get('platform_account', listing.platform_account)
        listing.minimum_price = data.get('minimum_price', listing.minimum_price)
        listing.maximum_price = data.get('maximum_price', listing.maximum_price)
        listing.bed_type = data.get('bed_type', listing.bed_type)
        listing.no_of_bed = data.get('no_of_bed', listing.no_of_bed)
        listing.updated_date = datetime.utcnow()
        listing.updated_by = current_user.username
        db.session.commit()
        return jsonify({'message': 'Listing updated successfully'}), 200



    # Delete a listing
    @app.route('/listings/<int:listing_id>', methods=['DELETE'])
    @login_required
    def delete_listing(listing_id):
        listing = Listings.query.get_or_404(listing_id)
        db.session.delete(listing)
        db.session.commit()
        return jsonify({'message': 'Listing deleted successfully'}), 200

    # New route to import earnings from a CSV file
    @app.route('/import_earnings', methods=['POST'])
    @login_required
    def import_earnings():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        source = request.form.get('source')
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and file.filename.endswith('.csv'):
            # Load data from CSV file
            try:
                # data = pd.read_csv(file, delimiter='\t', encoding='ISO-8859-1')
                data = pd.read_csv(file)
            except Exception as e:
                return jsonify({'error': f'Error reading CSV file: {str(e)}'}), 400

            # List to store invalid listings
            invalid_listings = []
            print(data)
            # Use the existing database connection
            with app.app_context():
                try:
                    # Iterate over the DataFrame from the last row to the first
                    for index in range(len(data) - 1, -1, -1):
                        row = data.iloc[index]
                        print(row)
                        listing_name = row['Listing'] if row['Listing'] != "nan" else ""
                        print(listing_name)
                        # Replace NaN values with None or a default value
                        row = row.where(pd.notnull(row), None)  # Replace NaN with None
                        row['Listing'] = row['Listing'] if pd.notna(row['Listing']) else "Unknown"  # Default for listing_name
                        row['Confirmation Code'] = row['Confirmation Code'] if pd.notna(row['Confirmation Code']) else ""  # Default for confirmation_code
                        row['Booking date'] = row['Booking date'] if pd.notna(row['Booking date']) else ""  # Default for booking_date
                        row['Start date'] = row['Start date'] if pd.notna(row['Start date']) else ""  # Default for start_date
                        row['End date'] = row['End date'] if pd.notna(row['End date']) else ""  # Default for end_date
                        row['Nights'] = row['Nights'] if pd.notna(row['Nights']) else 0  # Default for nights
                        row['Guest'] = row['Guest'] if pd.notna(row['Guest']) else "Unknown"  # Default for guest

                        # Check for specific types to import
                        if row['Type'] not in ["Reservation", "Adjustment", "Cancellation Fee", "Cancellation Fee Refund", "Misc Credit"]:
                            continue  # Skip this row if the type is not one of the specified values

                        # Convert date columns to the correct format
                        try:
                            #row['Date'] = parse_date(row['Date'])  # Use the new parse_date function
                            row['Date'] = parse_date(row['Date'])  # Use the new parse_date function
                            row['Arriving by date'] = parse_date(row['Arriving by date']) if row['Arriving by date'] else None
                            row['Booking date'] = parse_date(row['Booking date']) if row['Booking date'] else None
                            row['Start date'] = parse_date(row['Start date']) if row['Start date'] else None
                            row['End date'] = parse_date(row['End date']) if row['End date'] else None
                        except Exception as e:
                            print(f"Date conversion error at row {index}: {e}")
                            invalid_listings.append(index)  # Log the row index for invalid date conversion
                            continue  # Skip this iteration

                        if listing_name != "nan":
                            area_code = get_area_code(db,listing_name)  # Adjusted to use the function directly
                        else:
                            area_code = "Unknown"


                        query = """
                        INSERT INTO airbnb_earnings (Date, Arriving_by_date, Type, Confirmation_code, 
                                                    Booking_date, Start_date, End_date, Nights, Guest, 
                                                    Listing, Details, Reference_code, Currency, Amount, 
                                                    Paid_out, Service_fee, Fast_pay_fee, Cleaning_fee, 
                                                    Gross_earning, Occupancy_taxes, Area_code, Source) 
                        VALUES (:date, :arriving_by_date, :type, :confirmation_code, 
                                :booking_date, :start_date, :end_date, :nights, :guest, 
                                :listing, :details, :reference_code, :currency, :amount, 
                                :paid_out, :service_fee, :fast_pay_fee, :cleaning_fee, 
                                :gross_earning, :occupancy_taxes, :area_code, :source)
                        """
                        
                        db.session.execute(text(query), {
                            'date': row['Date'],
                            'arriving_by_date': row['Arriving by date'],
                            'type': row['Type'],
                            'confirmation_code': row['Confirmation Code'],
                            'booking_date': row['Booking date'],
                            'start_date': row['Start date'],
                            'end_date': row['End date'],
                            'nights': row['Nights'],
                            'guest': row['Guest'],
                            'listing': row['Listing'],
                            'details': row['Details'],
                            'reference_code': row['Reference code'],
                            'currency': row['Currency'],
                            'amount': row['Amount'],
                            'paid_out': row['Paid out'],
                            'service_fee': row['Service fee'],
                            'fast_pay_fee': row['Fast Pay Fee'],
                            'cleaning_fee': row['Cleaning fee'],
                            'gross_earning': row['Gross earnings'],
                            'occupancy_taxes': row['Occupancy taxes'],
                            'area_code': area_code,
                            'source': source
                        })
                    
                    db.session.commit()
                    # Log invalid listings after import completes
                    if invalid_listings:
                        print(f"Invalid listings found at rows: {invalid_listings}")
                    return jsonify({'message': 'Earnings imported successfully', 'invalid_listings': invalid_listings}), 200
                except Exception as e:
                    db.session.rollback()
                    print("There is an error in import_earnings")
                    print(e)
                    print(f"Unexpected error: {e}")
                    return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

        return jsonify({'error': 'Invalid file format'}), 400

    @app.route('/import_earnings_page', methods=['GET'])
    @login_required
    def import_earnings_page():
        return render_template('import_earnings.html')


    # Function to parse dates with multiple formats


    # Restrict access to all other pages for Deepan
    @app.route('/<path:path>')
    @login_required
    def restricted_access(path):
        print(current_user.username)
        if current_user.username == 'deepan':
            if path != '/' and path != '/deepan_report':  # Allow access only to the root page and Deepan's report page
                return 'Access denied', 403  # Forbidden access for Deepan
        elif current_user.username == 'slawek':
            if path != '/' and path != '/calendar':  # Allow access only to the root page and calendar page
                return 'Access denied', 403  # Forbidden access for Slawek
        # Handle other routes normally
        return 'This is a restricted page', 200  # Example response for other users
