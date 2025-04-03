from itsdangerous import URLSafeTimedSerializer
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from flask import render_template
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo
from dotenv import load_dotenv
from flask_migrate import Migrate
from datetime import date
from sqlalchemy import Column, Integer, TIMESTAMP, func
from datetime import datetime
from models.models import db, User, Riwayat, DoctorProfile
from flask_mail import Mail, Message
import os
import joblib
import numpy as np
import json
import sklearn

# Memuat model
model_path = os.path.join(os.getcwd(), 'storage/ml_models/model_entropy.pkl')
model = joblib.load(model_path)

# Memuat file .env
load_dotenv()

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Konfigurasi aplikasi Flask dengan SECRET_KEY, dan koneksi database menggunakan SQLAlchemy 
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey') 
#app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:root123@localhost/taflask?charset=utf8mb4')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_O6D4xutkfIFy@ep-withered-frost-a1h3mrq8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Inisialisasi ekstensi
mail = Mail(app)
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Nonaktifkan CSRF hanya untuk endpoint /predict
csrf.exempt("/predict")

# Inisialisasi serializer untuk token
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Form untuk Register menggunakan Flask-WTF
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_confirmation = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

# Form untuk Forgot Password
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

# Form untuk Reset Password
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])

# Rute halaman register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Menggunakan metode hashing 
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Menyimpan data ke database
        new_user = User(username=username, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Pendaftaran berhasil! Silakan login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}')

    return render_template('register.html', form=form)

# Rute halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Memeriksa apakah user ada di database
        user = User.query.filter_by(username=username).first()

        # Jika user ditemukan dan password sesuai
        if user and check_password_hash(user.password, password):
            # Menyimpan informasi login ke session
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login berhasil!')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah.')

    return render_template('login.html')

# Rute halaman Forgot Password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate token
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)

            # Kirim email
            msg = Message('Reset Password', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Untuk mereset password Anda, klik link berikut: {reset_url}'
            mail.send(msg)

            flash('Link reset password telah dikirim ke email Anda!')
        else:
            flash('Email tidak ditemukan!')

        return redirect(url_for('login'))

    return render_template('forgot_password.html', form=form)

# Route untuk Reset Password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Validasi token dan ambil email
        email = serializer.loads(token, salt='password-reset-salt', max_age=300)  # Token berlaku 15 menit
    except:
        flash('Link reset password tidak valid atau sudah kadaluarsa.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validasi password dan konfirmasi password
        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok.', 'danger')
            return redirect(url_for('reset_password', token=token))

        # Cari user berdasarkan email
        user = User.query.filter_by(email=email).first()
        if user:
            # Hash password baru
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            user.password = hashed_password
            db.session.commit()

            flash('Password berhasil direset. Silakan login dengan password baru.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email tidak ditemukan.', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', token=token)

# Rute halaman home
@app.route('/')
def home():
    return render_template('home.html')

# Daftar variabel dan label pertanyaan
feature_labels = {
    "HighBP": "Apakah Anda memiliki tekanan darah tinggi?",
    "GenHlth": "Bagaimana Anda menilai kesehatan Anda secara umum?",
    "HighChol": "Apakah Anda memiliki kolesterol tinggi?",
    "Age_Category": "Dalam kategori usia berapa Anda saat ini?",
    "BMI_Category": "Bagaimana kategori indeks massa tubuh (BMI) Anda?",
    "DiffWalk": "Apakah Anda mengalami kesulitan berjalan atau menaiki tangga?",
    "HeartDiseaseorAttack": "Apakah Anda pernah mengalami serangan jantung atau penyakit jantung koroner?",
    "Sex": "Apa jenis kelamin Anda?",
    "PhysHlth_Category": "Bagaimana kondisi kesehatan fisik Anda?",
    "PhysActivity": "Apakah Anda melakukan aktivitas fisik dalam 30 hari terakhir (tidak termasuk pekerjaan)?",
    "Veggies": "Apakah Anda mengonsumsi sayuran minimal satu kali sehari?",
    "Fruits": "Apakah Anda mengonsumsi buah minimal satu kali sehari?",
    "Stroke": "Apakah Anda pernah mengalami stroke?"
}

feature_choices = {
    "HighBP": [(0, "Tidak"), (1, "Ya")],
    "GenHlth": [(1, "Excellent"), (2, "Very Good"), (3, "Good"), (4, "Fair"), (5, "Poor")],
    "HighChol": [(0, "Tidak"), (1, "Ya")],
    "Age_Category": [],
    "BMI_Category": [],
    "DiffWalk": [(0, "Tidak"), (1, "Ya")],
    "HeartDiseaseorAttack": [(0, "Tidak"), (1, "Ya")],
    "Sex": [(0, "Perempuan"), (1, "Laki-Laki")],
    "PhysHlth_Category": [],
    "PhysActivity": [(0, "Tidak"), (1, "Ya")],
    "Veggies": [(0, "Tidak"), (1, "Ya")],
    "Fruits": [(0, "Tidak"), (1, "Ya")],
    "Stroke": [(0, "Tidak"), (1, "Ya")]
}

# Ambil nilai feature importance dari model
feature_importance = model.feature_importances_
sorted_features = sorted(zip(feature_labels.keys(), feature_importance), key=lambda x: x[1], reverse=True)
all_sorted_features = [f[0] for f in sorted_features] 

# Rute dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))

    username = session.get('username')
    selected_questions = {feature: feature_labels[feature] for feature in all_sorted_features}
    
    return render_template('dashboard.html', username=username, questions=selected_questions, choices=feature_choices)

# Rute predict
@app.route('/predict', methods=['POST'])
@csrf.exempt 
def predict():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))
    
    user_id = session['user_id']  # Ambil user_id dari session

    try:
        # Ambil data dari form
        name = request.form.get('name')
        features = request.form.getlist('features[]')  # Jawaban dari pertanyaan
        bmi_category = request.form.get('bmi_category')
        age_category = request.form.get('age_category')
        physhlth_category = request.form.get('physHlth_category')
        
        # Ambil nilai raw dari form
        raw_age = request.form.get('raw_Age')
        raw_bmi = request.form.get('raw_BMI')
        raw_physhlth = request.form.get('raw_PhysHlth')

        # Debugging: Cetak data yang diterima
        app.logger.info(f"Received name: {name}")
        app.logger.info(f"Received features: {features}")
        app.logger.info(f"Received BMI category: {bmi_category}")
        app.logger.info(f"Received Age category: {age_category}")
        app.logger.info(f"Received PhysHlth category: {physhlth_category}")
        app.logger.info(f"Received raw Age: {raw_age}")
        app.logger.info(f"Received raw BMI: {raw_bmi}")
        app.logger.info(f"Received raw PhysHlth: {raw_physhlth}")

        # Pastikan semua fitur diisi
        if not features or all(f == '' for f in features) or not bmi_category or not age_category or not physhlth_category:
            flash('Harap isi semua pertanyaan sebelum melakukan prediksi.', 'danger')
            return redirect(url_for('dashboard'))

        # Mapping untuk BMI
        bmi_mapping = {
            "Kurus (Underweight)": 1,
            "Normal (Ideal)": 2,
            "Gemuk (Overweight)": 0
        }

        if bmi_category not in bmi_mapping:
            flash('Terjadi kesalahan dalam perhitungan BMI.', 'danger')
            return redirect(url_for('dashboard'))

        bmi_value = bmi_mapping[bmi_category]

        # Mapping untuk Age_Category
        age_mapping = {
            "Bayi dan Balita": 1,
            "Anak-Anak": 0,
            "Remaja": 2,
            "Dewasa": 2,  
            "Lansia": 2   
        }

        if age_category not in age_mapping:
            flash('Terjadi kesalahan dalam kategori usia.', 'danger')
            return redirect(url_for('dashboard'))

        age_value = age_mapping[age_category]

        # Mapping untuk PhysHlth_Category
        physhlth_mapping = {
            "Sehat": 3,
            "Sedikit Tidak Sehat": 2,
            "Cukup Tidak Sehat": 0,
            "Sangat Tidak Sehat": 1
        }

        if physhlth_category not in physhlth_mapping:
            flash('Terjadi kesalahan dalam kategori kesehatan fisik.', 'danger')
            return redirect(url_for('dashboard'))

        physhlth_value = physhlth_mapping[physhlth_category]

        # Proses fitur yang diterima
        feature_dict = {}
        for feature in features:
            question_id, answer = feature.split(':')
            feature_dict[question_id] = int(answer) if answer.isdigit() else answer

        # Pastikan urutan fitur sesuai dengan yang diharapkan oleh model
        numeric_features = []
        for feature_name in all_sorted_features:
            if feature_name == "BMI_Category":
                numeric_features.append(bmi_value)
            elif feature_name == "Age_Category":
                numeric_features.append(age_value)
            elif feature_name == "PhysHlth_Category":
                numeric_features.append(physhlth_value)
            else:
                numeric_features.append(feature_dict.get(feature_name, 0))  # Default 0 jika tidak ada

        # Debugging: Cek fitur sebelum prediksi
        app.logger.info(f"Final features for prediction: {numeric_features}")

        # Konversi ke array numpy
        features_array = np.array(numeric_features).reshape(1, -1)

        # Lakukan prediksi
        prediction = model.predict(features_array)
        result = prediction[0] if isinstance(prediction, np.ndarray) else prediction
        prediction_string = "Beresiko Diabetes" if result == 1 else "Tidak Beresiko Diabetes"

        # Menyimpan data ke database
        new_riwayat = Riwayat(
            user_id=user_id,  
            name=name,
            HighBP=feature_dict.get("HighBP", 0),
            GenHlth=feature_dict.get("GenHlth", 0),
            HighChol=feature_dict.get("HighChol", 0),
            Age_Category=age_value,
            raw_Age=int(raw_age) if raw_age else None,  
            BMI_Category=bmi_value,
            raw_BMI=float(raw_bmi) if raw_bmi else None, 
            DiffWalk=feature_dict.get("DiffWalk", 0),
            HeartDiseaseorAttack=feature_dict.get("HeartDiseaseorAttack", 0),
            Sex=feature_dict.get("Sex", 0),
            PhysHlth_Category=physhlth_value,
            raw_PhysHlth=int(raw_physhlth) if raw_physhlth else None,  
            PhysActivity=feature_dict.get("PhysActivity", 0),
            Veggies=feature_dict.get("Veggies", 0),
            Fruits=feature_dict.get("Fruits", 0),
            Stroke=feature_dict.get("Stroke", 0),
            prediction=prediction_string
        )

        try:
            db.session.add(new_riwayat)
            db.session.commit()
            flash('Data berhasil disimpan', 'success')

            # Ambil riwayat terbaru hanya jika data berhasil disimpan
            latest_riwayat = Riwayat.query.filter_by(user_id=user_id).order_by(Riwayat.created_at.desc()).first()
            
            # Terjemahkan nilai fitur sebelum dikirim ke template
            translated_data = {
                "name": latest_riwayat.name,
                "prediction": latest_riwayat.prediction,
                "created_at": latest_riwayat.created_at.strftime('%d-%m-%Y'),
                "HighBP": translate_feature("HighBP", latest_riwayat.HighBP),
                "GenHlth": translate_feature("GenHlth", latest_riwayat.GenHlth),
                "HighChol": translate_feature("HighChol", latest_riwayat.HighChol),
                "Age_Category": translate_feature("Age_Category", latest_riwayat.Age_Category),
                "BMI_Category": translate_feature("BMI_Category", latest_riwayat.BMI_Category),
                "DiffWalk": translate_feature("DiffWalk", latest_riwayat.DiffWalk),
                "HeartDiseaseorAttack": translate_feature("HeartDiseaseorAttack", latest_riwayat.HeartDiseaseorAttack),
                "Sex": translate_feature("Sex", latest_riwayat.Sex),
                "PhysHlth_Category": translate_feature("PhysHlth_Category", latest_riwayat.PhysHlth_Category),
                "PhysActivity": translate_feature("PhysActivity", latest_riwayat.PhysActivity),
                "Veggies": translate_feature("Veggies", latest_riwayat.Veggies),
                "Fruits": translate_feature("Fruits", latest_riwayat.Fruits),
                "Stroke": translate_feature("Stroke", latest_riwayat.Stroke),
                "raw_Age": latest_riwayat.raw_Age,
                "raw_BMI": latest_riwayat.raw_BMI,
                "raw_PhysHlth": latest_riwayat.raw_PhysHlth,
            }

            return render_template('result.html', prediction=prediction_string, data=translated_data)

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            flash(f'Terjadi kesalahan saat menyimpan data: {str(e)}', 'danger')
            return redirect(url_for('dashboard'))  # Kembali ke dashboard jika terjadi error

    except Exception as e:
        app.logger.error(f"Prediction error: {str(e)}")
        flash(f'Terjadi kesalahan saat memproses prediksi: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

    
# Route untuk menampilkan riwayat
@app.route('/riwayat')
def riwayat():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))

    user_id = session['user_id']  # Ambil user_id dari session
    filter_name = request.args.get('name', '')

    # Query hanya riwayat milik user yang sedang login
    if filter_name:
        riwayat_data = Riwayat.query.filter_by(user_id=user_id).filter(Riwayat.name.contains(filter_name)).all()
    else:
        riwayat_data = Riwayat.query.filter_by(user_id=user_id).all()

    return render_template('riwayat.html', riwayat_data=riwayat_data, filter_name=filter_name)

# Route untuk menampilkan detail_prediksi
def translate_feature(feature_name, feature_value):
    """
    Menerjemahkan nilai integer dari fitur menjadi teks berdasarkan feature_choices.
    """
    # Handle khusus untuk BMI_Category
    if feature_name == "BMI_Category":
        bmi_mapping = {
            0: "Gemuk (Overweight)",
            1: "Kurus (Underweight)", 
            2: "Normal (Ideal)"
        }
        return bmi_mapping.get(feature_value, "Tidak Diketahui")
    
    # Handle khusus untuk Age_Category
    if feature_name == "Age_Category":
        age_mapping = {
            0: "Anak-Anak",
            1: "Bayi dan Balita",
            2: "Remaja",
            3: "Dewasa",  # Jika ada nilai tambahan
            4: "Lansia"   # Jika ada nilai tambahan
        }
        return age_mapping.get(feature_value, "Tidak Diketahui")
    
    # Handle khusus untuk PhysHlth_Category
    if feature_name == "PhysHlth_Category":
        physhlth_mapping = {
            0: "Cukup Tidak Sehat",
            1: "Sangat Tidak Sehat",
            2: "Sedikit Tidak Sehat",
            3: "Sehat"
        }
        return physhlth_mapping.get(feature_value, "Tidak Diketahui")
    
    # Untuk fitur lainnya
    choices = feature_choices.get(feature_name, [])
    for value, label in choices:
        if value == feature_value:
            return label
    return "Tidak Diketahui"

@app.route('/detail_prediksi/<int:id>')
def detail_prediksi(id):
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))
        
    # Ambil data berdasarkan ID
    data = Riwayat.query.get_or_404(id)

    # Terjemahkan nilai integer menjadi teks
    translated_data = {
        "name": data.name,
        "prediction": data.prediction,  # Perbaiki typo dari "prediction" ke "prediction"
        "created_at": data.created_at.strftime('%d-%m-%Y'),
        "HighBP": translate_feature("HighBP", data.HighBP),
        "GenHlth": translate_feature("GenHlth", data.GenHlth),
        "HighChol": translate_feature("HighChol", data.HighChol),
        "Age_Category": translate_feature("Age_Category", data.Age_Category),
        "BMI_Category": translate_feature("BMI_Category", data.BMI_Category),
        "DiffWalk": translate_feature("DiffWalk", data.DiffWalk),
        "HeartDiseaseorAttack": translate_feature("HeartDiseaseorAttack", data.HeartDiseaseorAttack),
        "Sex": translate_feature("Sex", data.Sex),
        "PhysHlth_Category": translate_feature("PhysHlth_Category", data.PhysHlth_Category),
        "PhysActivity": translate_feature("PhysActivity", data.PhysActivity),
        "Veggies": translate_feature("Veggies", data.Veggies),
        "Fruits": translate_feature("Fruits", data.Fruits),
        "Stroke": translate_feature("Stroke", data.Stroke),
        "raw_Age": data.raw_Age,
        "raw_BMI": data.raw_BMI,
        "raw_PhysHlth": data.raw_PhysHlth,
    }

    return render_template('detail_prediksi.html', data=translated_data)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('login'))

    doctor_profile = DoctorProfile.query.filter_by(user_email=user.email).first()

    if request.method == 'POST':
        # Update informasi profil
        full_name = request.form.get('full_name')
        str_number = request.form.get('str_number')
        specialization = request.form.get('specialization')
        hospital_name = request.form.get('hospital_name')
        phone_number = request.form.get('phone_number')

        if doctor_profile:
            # Jika profil sudah ada, update data
            doctor_profile.full_name = full_name
            doctor_profile.str_number = str_number
            doctor_profile.specialization = specialization
            doctor_profile.hospital_name = hospital_name
            doctor_profile.phone_number = phone_number
        else:
            # Jika profil belum ada, buat baru
            doctor_profile = DoctorProfile(
                full_name=full_name,
                str_number=str_number,
                specialization=specialization,
                hospital_name=hospital_name,
                phone_number=phone_number,
                user_email=user.email
            )
            db.session.add(doctor_profile)

        db.session.commit()
        flash('Profil berhasil diperbarui.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user, doctor_profile=doctor_profile)

@app.route('/update_account', methods=['POST'])
def update_account():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('login'))

    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_username:
        user.username = new_username

    if new_password:
        if new_password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok.', 'danger')
            return redirect(url_for('profile'))
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')

    db.session.commit()
    flash('Akun berhasil diperbarui.', 'success')
    return redirect(url_for('profile'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.')
    return redirect(url_for('login'))

@app.after_request
def add_header(response):
    # Menambahkan header untuk mencegah cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)