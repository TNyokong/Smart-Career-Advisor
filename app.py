from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import os

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# DB setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///career_advisor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class UserSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    interests = db.Column(db.Text, nullable=False)
    suggestion = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Admin user model
class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

# Train or load ML model
model_path = 'career_model.pkl'
if not os.path.exists(model_path):
    # Basic training data
    training_data = {
        "text": [
            "I love networks and routing",
            "Coding apps and software",
            "AI, data and automation",
            "Fixing computers and helping users",
        ],
        "label": [
            "Network Engineer",
            "Software Developer",
            "Machine Learning Engineer",
            "IT Support Technician",
        ]
    }
    df = pd.DataFrame(training_data)
    model = make_pipeline(TfidfVectorizer(), MultinomialNB())
    model.fit(df['text'], df['label'])
    joblib.dump(model, model_path)
else:
    model = joblib.load(model_path)

# Home
@app.route('/')
def index():
    return render_template("index.html")

# Predict suggestion
@app.route('/suggest', methods=['POST'])
def suggest():
    name = request.form['name']
    interests = request.form['interests']
    suggestion = model.predict([interests])[0]

    entry = UserSubmission(name=name, interests=interests, suggestion=suggestion)
    db.session.add(entry)
    db.session.commit()

    return render_template("result.html", name=name, suggestion=suggestion)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = AdminUser.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['admin'] = True
            return redirect(url_for('submissions'))
        else:
            flash('Invalid login credentials')
    return render_template('login.html')

# Register Admin (one-time setup route)
@app.route('/register')
def register():
    if AdminUser.query.filter_by(username='admin').first() is None:
        hashed_pw = generate_password_hash('Spane22')
        admin = AdminUser(username='admin', password_hash=hashed_pw)
        db.session.add(admin)
        db.session.commit()
        return "Admin registered. Now login with 'admin' and 'Spane22'"
    return "Admin already registered."

# Logout
@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out.')
    return redirect(url_for('login'))

# View all
@app.route('/submissions')
def submissions():
    if not session.get('admin'):
        return redirect(url_for('login'))
    all_submissions = UserSubmission.query.order_by(UserSubmission.timestamp.desc()).all()
    return render_template("submissions.html", submissions=all_submissions)

# Export CSV
@app.route('/export')
def export():
    if not session.get('admin'):
        return redirect(url_for('login'))
    submissions = UserSubmission.query.all()
    data = [{
        'Name': s.name,
        'Interests': s.interests,
        'Suggestion': s.suggestion,
        'Timestamp': s.timestamp
    } for s in submissions]
    df = pd.DataFrame(data)
    filepath = 'submissions_export.csv'
    df.to_csv(filepath, index=False)
    return send_file(filepath, as_attachment=True)

# Start app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)