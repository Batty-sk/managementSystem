class Config:
    SECRET_KEY = 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://dbsk:password1234@localhost/reservationsdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False