from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///names.db'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

class NameEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_name = db.Column(db.String(100), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_filename = db.Column(db.String(200))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/submit", methods=["GET", "POST"])
def submit_name():
    if request.method == "POST":
        name = request.form["name"]
        image = request.files.get("image")

        filename = None
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_entry = NameEntry(name=name, image_filename=filename)
        db.session.add(new_entry)
        db.session.commit()
        return redirect("/submit")

    return render_template("form.html")

@app.route("/names")
def show_names():
    entries = NameEntry.query.all()
    return render_template("names.html", entries=entries)

if __name__ == '__main__':
    app.run()
