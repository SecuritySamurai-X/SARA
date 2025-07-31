# SARA - Smart Alzheimer’s Reminder Assistant

SARA is a secure, multilingual reminder system designed for medical and caregiving use cases.

## 🔐 Features
💬 Voice-based medication and appointment reminders
🌐 Multilingual support using Google Text-to-Speech (gTTS)
🔑 Twilio OTP authentication for secure login/register
📅 Smart scheduling using APScheduler
👤 User registration, login, and session management
🧠 Cognitive-friendly UI with accessibility in mind
📜 History Log of All Reminders

## 🛠 Tech Stack

- Backend: Flask (Python)
- Frontend: HTML, CSS, JS
- Voice: Google Text-to-Speech (`gTTS`)
- Database: SQLite
- Authentication: Twilio OTP API
- Scheduler: APScheduler
- Voice Recognition: SpeechRecognition + PyAudio

## 📌 Future Improvements

- 📊 Health Stats Dashboard
- 📍 Geofencing with Alerts

## 🚀 How to Run
1. Clone the repository
```bash
git clone https://github.com/SecuritySamurai-X/SARA.git
```

2. Install the dependencies
```bash
pip install -r requirements.txt
```

4. Set environment variables
Create a .env file and add your Twilio credentials:
```env
TWILIO_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE=your_twilio_phone
```

4.Run the App
- python app.py
Then open http://localhost:5000 in your browser.

## 📷 Screenshots
- Login Page
<img width="1871" height="880" alt="image" src="https://github.com/user-attachments/assets/a564d831-7b48-4c6c-8c52-e7776c24a6df" />

<img width="1908" height="847" alt="image" src="https://github.com/user-attachments/assets/8ed54150-2e16-4701-a595-739026475986" />

- Appointment
  <img width="1463" height="865" alt="image" src="https://github.com/user-attachments/assets/e576aa1f-8571-42a8-958d-5da4eaae96c4" />

- Medication
  <img width="1494" height="882" alt="image" src="https://github.com/user-attachments/assets/a0e5b595-536b-4380-81ea-00996ce61333" />




