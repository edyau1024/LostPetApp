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

from geopy.geocoders import Nominatim

@app.route("/submit", methods=["GET", "POST"])
def submit_name():
    if request.method == "POST":
        pet_name = request.form["pet_name"]
        owner_name = request.form["owner_name"]
        location_text = request.form["location"]
        image = request.files.get("image")

        geolocator = Nominatim(user_agent="lostpet")
        location = geolocator.geocode(location_text)
        lat = location.latitude if location else None
        lng = location.longitude if location else None

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

@app.route("/ping")
def ping():
    return "pong"
    
if __name__ == '__main__':
    app.run()

