from models1 import db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus


load_dotenv()
app = Flask(__name__)

# PostgreSQL URI from .env
db_user = os.getenv('DB_USER')
db_password = quote_plus(os.getenv('DB_PASSWORD'))
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)




# When you want to only add new table
#with app.app_context():
    # This will create only the 'exams' table, if it doesn't exist yet
    #Exam.__table__.create(bind=db.engine, checkfirst=True)
    #print("✅ 'exams' table created successfully!")

