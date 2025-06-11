from flask import Flask
from app.routes.auth_routes import bp as auth_bp
from app.routes.user_routes import bp as user_bp
from app.routes.org_routes import bp as org_bp
from app.database import init_db
from dotenv import load_dotenv
import os
import json
from urllib.parse import quote_plus, urlencode


load_dotenv()

# PostgreSQL URI from .env
db_user = os.getenv('DB_USER')
db_password = quote_plus(os.getenv('DB_PASSWORD'))
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_db(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(org_bp)

    return app

app = create_app()

@app.route("/")
def index():
    return "TEXAM API is running!"

if __name__ == "__main__":
    app.run(port=8080)

