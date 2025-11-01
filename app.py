from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///names.db'
db = SQLAlchemy(app)

class NameEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/submit", methods=["GET", "POST"])
def submit_name():
    if request.method == "POST":
        name = request.form["name"]
        new_entry = NameEntry(name=name)
        db.session.add(new_entry)
        db.session.commit()
        return redirect("/submit")
    return render_template("form.html")

if __name__ == '__main__':
    app.run()

@app.route("/names")
def show_names():
    entries = NameEntry.query.all()
    return render_template("names.html", entries=entries)

class NameEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_filename = db.Column(db.String(200))  # New field

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
