from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from gtts import gTTS
from twilio.rest import Client
import uuid
import random
import datetime
from io import BytesIO
import pygame
import speech_recognition as sr
import time
import os
from flask import flash
from werkzeug.utils import secure_filename


app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reminders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SCHEDULER_API_ENABLED'] = True

db = SQLAlchemy(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

texts = {
    "English": "Time to take your medicine. Have you taken it?",
    "Hindi": "दवा लेने का समय है। क्या आपने ली है?",
    "Kannada": "ಔಷಧ ತಗ್ಗೊಳ್ಳುವ ಸಮಯವಾಗಿದೆ. ನೀವು ತಗೊಂಡಿದ್ದೀರಾ?"
}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    otp = db.Column(db.String(6))

class Reminder(db.Model):
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    time = db.Column(db.String, nullable=False)
    language = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False, default="Time to take your medicine.")
    response = db.Column(db.String, default="Pending")

class Appointment(db.Model):
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    doctor = db.Column(db.String, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def play_audio(filename):
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()

def play_beep():
    beep_tts = gTTS(text="Beep", lang='en')
    beep_tts.save("beep.mp3")
    play_audio("beep.mp3")

def listen_for_reply(lang):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language=lang[:2].lower())
            return text.lower()
        except:
            return "unclear"

def trigger_reminder(lang):
    reminder_text = texts.get(lang.capitalize(), texts['English'])
    tts = gTTS(text=reminder_text, lang=lang[:2].lower())
    tts.save('reminder.mp3')
    play_audio('reminder.mp3')
    time.sleep(1)
    play_beep()
    print("Listening for user response...")
    response = listen_for_reply(lang)
    print(f"User responded: {response}")
    if response not in ['yes', 'हाँ', 'ಹೌದು']:
        retry_text = "You said no or unclear. I will remind you again in one minute."
        retry_tts = gTTS(text=retry_text, lang=lang[:2].lower())
        retry_tts.save('retry.mp3')
        play_audio('retry.mp3')
        time.sleep(60)
        trigger_reminder(lang)

def speak_reminder(reminder_id):
    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return
    print(f"[Reminder Triggered] Time: {reminder.time}, Language: {reminder.language}")
    trigger_reminder(reminder.language)
    response = listen_for_reply(reminder.language)
    if any(word in response for word in ['yes', 'हाँ', 'ಹೌದು']):
        reminder.response = "Taken"
    elif any(word in response for word in ['no', 'नहीं', 'ಇಲ್ಲ']):
        reminder.response = "Not Taken"
    else:
        reminder.response = "Unclear"
    db.session.commit()

@app.route('/')
@login_required
def home():
    reminders = Reminder.query.filter_by(user_id=current_user.id).order_by(Reminder.time).limit(5).all()
    return render_template('index.html', reminders=reminders)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        user = User(username=username, password=password, phone=phone)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            db.session.commit()
            to_number = user.phone
            if not to_number.startswith('+'):
                to_number = '+91' + to_number
            client.messages.create(
                to=to_number,
                from_=TWILIO_PHONE,
                body=f"Your OTP is {otp}"
            )
            session['temp_user'] = user.id
            return redirect('/verify')
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        input_otp = request.form['otp']
        temp_user = User.query.get(session.get('temp_user'))
        if temp_user and temp_user.otp == input_otp:
            login_user(temp_user)
            return redirect('/')
    return render_template('verify.html')



@app.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect('/login')

@app.route('/appointments')
@login_required
def appointments():
    return render_template('appointments.html')

@app.route('/medication')
@login_required
def medication():
    return render_template('medication.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/submit_medication_response', methods=['POST'])
@login_required
def submit_medication_response():
    data = request.json
    response = data.get('response')

   
    reminder = Reminder.query.filter_by(user_id=current_user.id).order_by(Reminder.time.desc()).first()
    if reminder:
        reminder.response = response
        db.session.commit()
        return jsonify({"status": response})
    return jsonify({"status": "No reminder found"})


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['photo']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            filename = secure_filename(f"{current_user.id}.jpg")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash('Profile image uploaded successfully.')
            return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


@app.route('/save_reminder', methods=['POST'])
@login_required
def save_reminder():
    data = request.json
    reminder_id = str(uuid.uuid4())
    time_str = data['time']
    language = data['language']
    message = data.get('message', texts[language])
    new_reminder = Reminder(
        id=reminder_id,
        user_id=current_user.id,
        time=time_str,
        language=language,
        message=message
    )
    db.session.add(new_reminder)
    db.session.commit()

    hr, minute = map(int, time_str.split(':'))
    now = datetime.datetime.now()
    run_time = now.replace(hour=hr, minute=minute, second=0, microsecond=0)
    if run_time < now:
        run_time += datetime.timedelta(days=1)

    scheduler.add_job(
        id=reminder_id,
        func=speak_reminder,
        args=[reminder_id],
        trigger='date',
        run_date=run_time
    )
    return jsonify({"status": "success", "id": reminder_id})

@app.route('/skip-login')
def skip_login():
    demo_user = User.query.filter_by(username="guest").first()

    if not demo_user:
        demo_user = User(username="guest", password="guest123", phone="+910000000000")
        db.session.add(demo_user)
        db.session.commit()

    login_user(demo_user)
    return redirect('/')



# Run server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)
