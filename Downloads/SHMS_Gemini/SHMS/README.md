# 🏥 Smart Health Monitoring System (SHMS)

> An AI-powered web app that monitors daily health data and predicts risks for Diabetes, Hypertension, and Stress using Machine Learning.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![ML](https://img.shields.io/badge/ML-Scikit--learn-orange?logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌟 Features

| Feature | Description |
|---|---|
| 🔐 Authentication | Secure register, login, logout |
| 📋 Health Logging | Weight, BP, Sugar, Sleep, Exercise, Mood, Stress |
| 🤖 AI Predictions | Diabetes · Hypertension · Stress risk % |
| 🚨 Smart Alerts | Real-time warnings when vitals are critical |
| 💡 Recommendations | Personalized tips based on your actual data |
| 📈 Charts | Interactive Plotly trends (7D / 30D / 90D) |
| 📄 PDF Reports | Professional downloadable health reports |
| 📤 CSV | Import and export all your health data |

---

## ⚡ Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/SHMS.git
cd SHMS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python run.py

# 4. Open browser
# http://127.0.0.1:5000
```

---

## 🚀 Deploy on Render (Free)

1. Fork this repo
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Deploy**
5. Your app goes live at `https://shms-xxxx.onrender.com`

---

## 🛠️ Tech Stack

```
Backend  : Python 3.10+, Flask, SQLAlchemy, Flask-Login
Database : SQLite
ML       : Scikit-learn (Logistic Regression + Decision Tree)
Charts   : Plotly.js
PDF      : ReportLab
Frontend : HTML5, CSS3, Vanilla JS
Deploy   : Gunicorn + Render
```

---

## 📁 Project Structure

```
SHMS/
├── app/
│   ├── routes/          # auth, main, health, ai, charts, reports
│   ├── templates/       # HTML pages (dark UI)
│   ├── ml_engine.py     # AI risk prediction engine
│   ├── pdf_generator.py # PDF report generator
│   └── models.py        # Database models
├── config.py
├── run.py
├── Procfile             # For deployment
├── render.yaml          # Render.com config
└── requirements.txt
```

---

## 🤖 How the AI Works

The ML engine trains on **medically-grounded synthetic data** (2000 samples) using two models:

- **Logistic Regression** — 55% weight
- **Decision Tree** — 45% weight

Predictions for 3 risks:
- **Diabetes** — sugar level, weight, exercise, age
- **Hypertension** — blood pressure, stress, sleep, exercise
- **Stress** — stress level, sleep, mood, exercise

---

## ⚕️ Disclaimer

For informational purposes only. Not a substitute for professional medical advice.
