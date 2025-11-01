from flask_sqlalchemy import SQLAlchemy
from flask import request, redirect, render_template

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///names.db'
db = SQLAlchemy(app)

class NameEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()


from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()


@app.route("/submit", methods=["GET", "POST"])
def submit_name():
    if request.method == "POST":
        name = request.form["name"]
        new_entry = NameEntry(name=name)
        db.session.add(new_entry)
        db.session.commit()
        return redirect("/submit")
    return render_template("form.html")
    
