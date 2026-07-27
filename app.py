import os
from flask import Flask, request, redirect, render_template, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import googlemaps
from azure.storage.blob import BlobServiceClient
import uuid

# -------------------------------
# PATHS
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "names.db")

# -------------------------------
# FLASK APP SETUP
# -------------------------------
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default-secret")

# Configure AFTER app is created
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------------------------
# DATABASE
# -------------------------------
db = SQLAlchemy(app)

class NameEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_name = db.Column(db.String(100), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    formatted_address = db.Column(db.String(200), nullable=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    image_filename = db.Column(db.String(200))
    phone_number = db.Column(db.String(20), nullable=True)
    date_lost = db.Column(db.String(20), nullable=True)
    reward = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------------
# SAFE GOOGLE MAPS CLIENT LOADER
# -------------------------------
def get_gmaps():
    key = os.environ.get("GOOGLE_GEOCODING_KEY")
    if not key:
        raise RuntimeError("GOOGLE_GEOCODING_KEY is missing")
    return googlemaps.Client(key=key)

# -------------------------------
# BLOB STORAGE SETUP
# -------------------------------
BLOB_CONTAINER_NAME = "images"

def get_blob_container():
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is missing")
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    return blob_service_client, blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

# -------------------------------
# ROUTES
# -------------------------------
@app.route('/test-static')
def test_static():
    static_dir = os.path.join(app.root_path, 'static')
    return send_from_directory(static_dir, 'TestAutocomplete.html')

@app.route("/init-db")
def init_db():
    try:
        with app.app_context():
            db.create_all()
            app.logger.info("db.create_all() executed")
            app.logger.info(f"DB path: {app.config['SQLALCHEMY_DATABASE_URI']}")
        return "Database initialized."
    except Exception as e:
        app.logger.error(f"init-db error: {e}")
        return f"Error: {e}", 500

@app.route("/submit", methods=["GET", "POST"])
def submit_name():
    try:
        if request.method == "POST":
            pet_name = request.form.get("pet_name", "").strip()
            if not pet_name or len(pet_name) < 2:
                flash("Pet name is required and must be at least 2 characters.")
                return redirect("/submit")

            owner_name = request.form["owner_name"]
            location_text = request.form.get("location", "").strip()
            app.logger.info(f"Geocoding input: '{location_text}'")

            place_id = request.form.get("place_id")
            formatted_address = request.form.get("formatted_address")
            lat = lng = None

            if not place_id:
                flash("Please select a suggested address from the dropdown.")
                return redirect("/submit")

            try:
                gmaps = get_gmaps()
                geocode_result = gmaps.place(place_id=place_id)
                result = geocode_result.get("result", {})
                location = result.get("geometry", {}).get("location", {})
                lat = location.get
