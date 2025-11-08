from flask import flash
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default-secret")
from flask import Flask, request, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
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
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    image_filename = db.Column(db.String(200))
    phone_number = db.Column(db.String(20), nullable=True)
    date_lost = db.Column(db.String(20), nullable=True)  # Use db.Date if you want strict date handling
    reward = db.Column(db.Float, nullable=True)

with app.app_context():
    db.create_all()

import googlemaps

gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_GEOCODING_KEY"))

from azure.storage.blob import BlobServiceClient
import uuid

# Setup (place this near the top of your file, after imports)
blob_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
blob_container_name = "images"
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
container_client = blob_service_client.get_container_client(blob_container_name)

@app.route("/submit", methods=["GET", "POST"])
def submit_name():
    try:
        if request.method == "POST":
            pet_name = request.form.get("pet_name", "").strip()
            if not pet_name:
                flash("Pet name is required.")
                return redirect("/submit")
            if len(pet_name) < 2:
                flash("Pet name must be at least 2 characters.")
                return redirect("/submit")
            owner_name = request.form["owner_name"]
            location_text = request.form["location"]
            phone_number = request.form.get("phone_number")
            date_lost = request.form.get("date_lost")
            reward_raw = request.form.get("reward")
            try:
                reward = float(reward_raw) if reward_raw else None
            except ValueError:
                flash("Reward must be a number.")
                return redirect("/submit")
            image = request.files.get("image")
    
            # Geocode using Google Maps
            geocode_result = gmaps.geocode(location_text)
            lat = lng = None
            if geocode_result:
                lat = geocode_result[0]["geometry"]["location"]["lat"]
                lng = geocode_result[0]["geometry"]["location"]["lng"]
            else:
                app.logger.warning(f"No geocode result for: {location_text}")

            image_url = None

           
            # Inside your POST handler:
            if image and image.filename:
                filename = secure_filename(image.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                blob_client = container_client.get_blob_client(unique_filename)
                blob_client.upload_blob(image, overwrite=True)
                image_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{blob_container_name}/{unique_filename}"
            else:
                image_url = None                        

            new_entry = NameEntry(
                pet_name=pet_name,
                owner_name=owner_name,
                location=location_text,
                lat=lat,
                lng=lng,
                image_filename=image_url,
                phone_number=phone_number,
                date_lost=date_lost,
                reward=reward
            )
            db.session.add(new_entry)
            db.session.commit()
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
    
if __name__ == '__main__':
    app.run()

