from flask import Flask, request, redirect, render_template
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

with app.app_context():
    db.create_all()

import googlemaps

gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_GEOCODING_KEY"))

@app.route("/submit", methods=["GET", "POST"])
def submit_name():
    try:
        if request.method == "POST":
            pet_name = request.form["pet_name"]
            owner_name = request.form["owner_name"]
            location_text = request.form["location"]
            image = request.files.get("image")
    
            # Geocode using Google Maps
            geocode_result = gmaps.geocode(location_text)
            lat = lng = None
            if geocode_result:
                lat = geocode_result[0]["geometry"]["location"]["lat"]
                lng = geocode_result[0]["geometry"]["location"]["lng"]
            else:
                app.logger.warning(f"No geocode result for: {location_text}")

            filename = None
            if image and image.filename:
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            new_entry = NameEntry(
                pet_name=pet_name,
                owner_name=owner_name,
                location=location_text,
                lat=lat,
                lng=lng,
                image_filename=filename
            )
            db.session.add(new_entry)
            db.session.commit()
            return redirect("/submit")
    
        return render_template("form.html")
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
        
@app.route("/ping")
def ping():
    return "pong"
    
if __name__ == '__main__':
    app.run()

