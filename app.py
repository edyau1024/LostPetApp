import os
from flask import Flask, request, redirect, render_template, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import googlemaps
from azure.storage.blob import BlobServiceClient
import uuid

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default-secret")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/site/wwwroot/names.db'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
blob_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
blob_container_name = "images"
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
container_client = blob_service_client.get_container_client(blob_container_name)

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
                lat = location.get("lat")
                lng = location.get("lng")
                if not formatted_address:
                    formatted_address = result.get("formatted_address")
            except Exception as e:
                app.logger.error(f"Geocoding failed for place_id {place_id}: {e}")
                flash("Geocoding failed. Please try again.")
                return redirect("/submit")

            phone_number = request.form.get("phone_number")
            date_lost = request.form.get("date_lost")
            reward_raw = request.form.get("reward")
            try:
                reward = float(reward_raw) if reward_raw else None
            except ValueError:
                flash("Reward must be a number.")
                return redirect("/submit")

            image = request.files.get("image")
            image_url = None
            if image and image.filename:
                filename = secure_filename(image.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                blob_client = container_client.get_blob_client(unique_filename)
                blob_client.upload_blob(image, overwrite=True)
                image_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{blob_container_name}/{unique_filename}"

            new_entry = NameEntry(
                pet_name=pet_name,
                owner_name=owner_name,
                location=location_text,
                formatted_address=formatted_address,
                lat=lat,
                lng=lng,
                image_filename=image_url,
                phone_number=phone_number,
                date_lost=date_lost,
                reward=reward
            )
            db.session.add(new_entry)
            db.session.commit()
            app.logger.info(f"New entry submitted: {pet_name} at {formatted_address}")
            return redirect("/submit")

        return render_template("form.html", google_api_key=os.environ.get("GOOGLE_GEOCODING_KEY"))
    except Exception as e:
        app.logger.error(f"Form submission error: {e}")
        return "Internal Server Error", 500

@app.route("/names", endpoint="show_names")
def show_names():
    entries = NameEntry.query.all()
    return render_template("names.html", entries=entries)

@app.route('/')
def home():
    try:
        entries = NameEntry.query.all()
        return render_template("home.html", entries=entries)
    except Exception as e:
        app.logger.error(f"Home page error: {e}")
        return "Internal Server Error", 500

@app.route("/test-geocode")
def test_geocode():
    try:
        gmaps = get_gmaps()
        result = gmaps.geocode("123 Main St, Vancouver, BC")
        app.logger.info(f"Test geocode result: {result}")
        return str(result[0]["geometry"]["location"])
    except Exception as e:
        app.logger.error(f"Geocoding error: {e}")
        return f"Geocoding error: {e}", 500

@app.route('/delete/<int:id>', methods=['POST'])
def delete_entry(id):
    entry = NameEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('show_names'))

@app.route("/ping")
def ping():
    return "pong"
