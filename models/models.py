from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Model User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relasi ke Riwayat (satu pengguna bisa memiliki banyak riwayat)
    riwayats = db.relationship('Riwayat', backref='user', lazy=True)

class DoctorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    str_number = db.Column(db.String(50), nullable=False)  
    specialization = db.Column(db.String(100), nullable=False)  
    hospital_name = db.Column(db.String(150), nullable=False)  
    phone_number = db.Column(db.String(20), nullable=False)  
    user_email = db.Column(db.String(120), db.ForeignKey('user.email'), unique=True, nullable=False)

# Model Riwayat
class Riwayat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    HighBP = db.Column(db.Integer, nullable=False)
    GenHlth = db.Column(db.Integer, nullable=False)
    HighChol = db.Column(db.Integer, nullable=False)
    Age_Category = db.Column(db.Integer, nullable=False)  # Nilai yang dipetakan untuk prediksi
    raw_Age = db.Column(db.Integer, nullable=True)  # Nilai raw (asli, misal: 13)
    BMI_Category = db.Column(db.Integer, nullable=False)  # Nilai yang dipetakan untuk prediksi
    raw_BMI = db.Column(db.Float, nullable=True)  # Nilai raw (asli, misal: 22.5)
    DiffWalk = db.Column(db.Integer, nullable=False)
    HeartDiseaseorAttack = db.Column(db.Integer, nullable=False)
    Sex = db.Column(db.Integer, nullable=False)
    PhysHlth_Category = db.Column(db.Integer, nullable=False)  # Nilai yang dipetakan untuk prediksi
    raw_PhysHlth = db.Column(db.Integer, nullable=True)  # Nilai raw (asli, misal: 5)
    PhysActivity = db.Column(db.Integer, nullable=False)
    Veggies = db.Column(db.Integer, nullable=False)
    Fruits = db.Column(db.Integer, nullable=False)
    Stroke = db.Column(db.Integer, nullable=False)
    prediction = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)