from flask import Flask
from flask_login import LoginManager
import os
from dotenv import load_dotenv
from extensions import db
import logging
from routes import register_routes
from models import User




load_dotenv()
# Configure logging
logging.basicConfig(filename='hostcrmapp.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Add a secret key for session management

# MySQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost/reservationsdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


users = [
    User(id=72, username='consultant', passkey='123456', access_pages=['home', 'bookings', 'earnings']),
    User(id=7, username='deepan', passkey='449531', access_pages=['home', 'deepan_report']),  # New user added
    User(id=9, username='slawek', passkey='567434', access_pages=['home', 'calendar']),  # New user added
]


@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user.id == int(user_id):
            return user
    return None

earnings = []  # Initialize the global earnings variable

# Read all listings
register_routes(app,db)

if __name__ == '__main__':
    print('running the flask server...')
    with app.app_context():
        db.create_all() 
    app.run(debug=True, host='0.0.0.0', port=8000)
    

