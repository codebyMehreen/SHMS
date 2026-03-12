"""
SHMS AI Engine
==============
Trains Logistic Regression + Decision Tree models on synthetic health data
and provides real-time risk predictions for each user entry.

Risks predicted:
  1. Diabetes Risk     (based on sugar, weight, age, exercise)
  2. Hypertension Risk (based on BP, stress, sleep, exercise)
  3. Stress Risk       (based on stress_level, sleep, mood, exercise)

No external dataset needed — uses medically-grounded synthetic data.
"""

import numpy as np
import joblib, os
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# ── Synthetic training data ────────────────────────────────────────────────

def _generate_data(n=2000, seed=42):
    rng = np.random.default_rng(seed)

    age              = rng.integers(18, 80, n).astype(float)
    weight           = rng.uniform(45, 130, n)
    sugar            = rng.uniform(60, 300, n)
    systolic         = rng.uniform(90, 180, n)
    diastolic        = rng.uniform(60, 120, n)
    sleep            = rng.uniform(3, 10, n)
    exercise         = rng.uniform(0, 120, n)
    mood             = rng.uniform(1, 10, n)
    stress           = rng.uniform(1, 10, n)

    # Diabetes: high sugar + high weight + low exercise + older age
    diabetes_score = (
        (sugar - 100) / 50 +
        (weight - 70) / 30 +
        (70 - exercise) / 40 +
        (age - 40) / 20
    )
    diabetes = (diabetes_score + rng.normal(0, 0.5, n) > 1.2).astype(int)

    # Hypertension: high BP + high stress + low sleep + low exercise
    bp_mean = (systolic * 0.6 + diastolic * 0.4)
    hyper_score = (
        (bp_mean - 100) / 30 +
        (stress - 5) / 3 +
        (6 - sleep) / 2 +
        (60 - exercise) / 40
    )
    hypertension = (hyper_score + rng.normal(0, 0.5, n) > 1.0).astype(int)

    # High stress: high stress level + low sleep + low mood + low exercise
    stress_score = (
        (stress - 5) / 2 +
        (6 - sleep) / 2 +
        (5 - mood) / 3 +
        (40 - exercise) / 40
    )
    high_stress = (stress_score + rng.normal(0, 0.4, n) > 0.8).astype(int)

    X = np.column_stack([
        age, weight, sugar, systolic, diastolic,
        sleep, exercise, mood, stress
    ])
    return X, diabetes, hypertension, high_stress


# ── Train & save models ────────────────────────────────────────────────────

def train_models():
    X, y_diabetes, y_hyper, y_stress = _generate_data()

    targets = {
        'diabetes':     y_diabetes,
        'hypertension': y_hyper,
        'stress':       y_stress,
    }

    for name, y in targets.items():
        # Logistic Regression
        lr = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(max_iter=1000, random_state=42))
        ])
        lr.fit(X, y)
        joblib.dump(lr, os.path.join(MODEL_DIR, f'{name}_lr.pkl'))

        # Decision Tree
        dt = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', DecisionTreeClassifier(max_depth=6, random_state=42))
        ])
        dt.fit(X, y)
        joblib.dump(dt, os.path.join(MODEL_DIR, f'{name}_dt.pkl'))

    print("✅ All models trained and saved.")


def _load_or_train(name, model_type='lr'):
    path = os.path.join(MODEL_DIR, f'{name}_{model_type}.pkl')
    if not os.path.exists(path):
        train_models()
    return joblib.load(path)


# ── Feature vector from entry ──────────────────────────────────────────────

def _entry_to_features(entry, user_age=35):
    """Convert a HealthEntry (or dict) to a feature array."""
    def g(key, default):
        if hasattr(entry, key):
            val = getattr(entry, key)
        elif isinstance(entry, dict):
            val = entry.get(key)
        else:
            val = None
        return float(val) if val is not None else float(default)

    return np.array([[
        g('age',              user_age),
        g('weight',           70),
        g('sugar_level',      90),
        g('systolic_bp',      120),
        g('diastolic_bp',     80),
        g('sleep_hours',      7),
        g('exercise_minutes', 30),
        g('mood',             7),
        g('stress_level',     4),
    ]])


# ── Main prediction function ───────────────────────────────────────────────

def predict_risks(entry, user_age=35):
    """
    Returns a dict with risk scores and labels for all three risks.
    Combines LR + DT probabilities for a more robust prediction.
    """
    features = _entry_to_features(entry, user_age)

    results = {}
    for risk in ['diabetes', 'hypertension', 'stress']:
        lr = _load_or_train(risk, 'lr')
        dt = _load_or_train(risk, 'dt')

        prob_lr = lr.predict_proba(features)[0][1]
        prob_dt = dt.predict_proba(features)[0][1]
        prob    = round((prob_lr * 0.55 + prob_dt * 0.45) * 100, 1)

        if prob >= 70:
            level, color = 'High',    'danger'
        elif prob >= 40:
            level, color = 'Moderate','warning'
        else:
            level, color = 'Low',     'success'

        results[risk] = {
            'probability': prob,
            'level':       level,
            'color':       color,
        }

    # Overall risk score (weighted average)
    overall = round(
        results['diabetes']['probability']     * 0.35 +
        results['hypertension']['probability'] * 0.40 +
        results['stress']['probability']       * 0.25,
        1
    )
    if overall >= 65:
        overall_level, overall_color = 'High Risk',      'danger'
    elif overall >= 35:
        overall_level, overall_color = 'Moderate Risk',  'warning'
    else:
        overall_level, overall_color = 'Low Risk',       'success'

    results['overall'] = {
        'score':  overall,
        'level':  overall_level,
        'color':  overall_color,
    }
    return results


# ── Alerts ─────────────────────────────────────────────────────────────────

def get_alerts(entry):
    alerts = []

    def g(key):
        if hasattr(entry, key): return getattr(entry, key)
        if isinstance(entry, dict): return entry.get(key)
        return None

    bp_sys  = g('systolic_bp')
    bp_dia  = g('diastolic_bp')
    sugar   = g('sugar_level')
    sleep   = g('sleep_hours')
    stress  = g('stress_level')
    mood    = g('mood')
    weight  = g('weight')
    exercise = g('exercise_minutes')

    if bp_sys and bp_sys >= 140:
        alerts.append({'type':'danger',  'icon':'🚨', 'title':'Hypertensive Range',
                       'msg': f'Systolic BP {bp_sys} mmHg is dangerously high. Seek medical advice immediately.'})
    elif bp_sys and bp_sys >= 130:
        alerts.append({'type':'warning', 'icon':'⚠️', 'title':'Elevated Blood Pressure',
                       'msg': f'BP {bp_sys}/{bp_dia} mmHg is above normal. Monitor closely.'})

    if sugar and sugar >= 200:
        alerts.append({'type':'danger',  'icon':'🚨', 'title':'Very High Blood Sugar',
                       'msg': f'Sugar level {sugar} mg/dL is critically high. Consult a doctor.'})
    elif sugar and sugar >= 126:
        alerts.append({'type':'danger',  'icon':'🔴', 'title':'Diabetic Range Sugar',
                       'msg': f'Fasting sugar {sugar} mg/dL indicates possible diabetes.'})
    elif sugar and sugar >= 100:
        alerts.append({'type':'warning', 'icon':'⚡', 'title':'Pre-diabetic Sugar Level',
                       'msg': f'Sugar {sugar} mg/dL is in pre-diabetic range. Reduce sugar intake.'})

    if sleep and sleep < 5:
        alerts.append({'type':'danger',  'icon':'😴', 'title':'Severe Sleep Deprivation',
                       'msg': f'Only {sleep} hours of sleep. Minimum 7 hours recommended.'})
    elif sleep and sleep < 7:
        alerts.append({'type':'warning', 'icon':'🌙', 'title':'Insufficient Sleep',
                       'msg': f'{sleep} hours of sleep is below the recommended 7–9 hours.'})

    if stress and stress >= 8:
        alerts.append({'type':'danger',  'icon':'🤯', 'title':'Critical Stress Level',
                       'msg': f'Stress level {stress}/10 is dangerously high. Take immediate action.'})
    elif stress and stress >= 6:
        alerts.append({'type':'warning', 'icon':'😤', 'title':'High Stress Detected',
                       'msg': f'Stress level {stress}/10. Try meditation or light exercise.'})

    if mood and mood <= 3:
        alerts.append({'type':'warning', 'icon':'💙', 'title':'Low Mood Detected',
                       'msg': 'Your mood score is low. Consider talking to someone you trust.'})

    if exercise is not None and exercise == 0:
        alerts.append({'type':'warning', 'icon':'🏃', 'title':'No Exercise Today',
                       'msg': 'Even 15–20 minutes of walking significantly improves health.'})

    return alerts


# ── Personalized recommendations ──────────────────────────────────────────

def get_recommendations(entry, risks):
    recs = []

    def g(key):
        if hasattr(entry, key): return getattr(entry, key)
        if isinstance(entry, dict): return entry.get(key)
        return None

    sugar    = g('sugar_level')
    bp_sys   = g('systolic_bp')
    sleep    = g('sleep_hours')
    exercise = g('exercise_minutes')
    stress   = g('stress_level')
    weight   = g('weight')
    mood     = g('mood')

    d_risk = risks.get('diabetes',     {}).get('probability', 0)
    h_risk = risks.get('hypertension', {}).get('probability', 0)
    s_risk = risks.get('stress',       {}).get('probability', 0)

    logged_any = any([sugar, bp_sys, sleep, exercise, stress, mood, weight])
    if not logged_any:
        recs.append({'category':'📋 Log More Data', 'color':'blue',
                     'tip': 'Fill in more health fields (sugar, BP, sleep, exercise, stress) to get personalized recommendations tailored to your actual health data.'})
        return recs

    # Diet — only if sugar was logged OR diabetes risk is high
    if sugar is not None:
        if sugar >= 126:
            recs.append({'category':'🥗 Diet — High Sugar', 'color':'red',
                         'tip': f'Your sugar is {sugar} mg/dL (diabetic range). Cut all refined sugars, white rice, and white bread immediately. Choose vegetables, legumes, and high-fiber foods.'})
        elif sugar >= 100:
            recs.append({'category':'🥗 Diet — Watch Sugar', 'color':'orange',
                         'tip': f'Your sugar is {sugar} mg/dL (pre-diabetic range). Reduce sweets, sugary drinks, and processed carbs. Add more fiber and protein to your meals.'})
        else:
            recs.append({'category':'🥗 Diet — Good', 'color':'green',
                         'tip': f'Your sugar level ({sugar} mg/dL) is healthy. Keep eating balanced meals with vegetables, lean protein, and whole grains to maintain it.'})
    elif d_risk >= 50:
        recs.append({'category':'🥗 Diet', 'color':'orange',
                     'tip': 'Your AI diabetes risk is elevated. Consider logging your sugar level and reducing refined carbs and sugary drinks.'})

    # Sodium — only if BP was logged AND is high
    if bp_sys is not None:
        if bp_sys >= 140:
            recs.append({'category':'🧂 Sodium — Critical', 'color':'red',
                         'tip': f'BP {bp_sys} mmHg is dangerously high. Immediately reduce salt to under 1,500mg/day. Avoid all processed food, fast food, and pickles.'})
        elif bp_sys >= 130:
            recs.append({'category':'🧂 Sodium — Reduce', 'color':'orange',
                         'tip': f'BP {bp_sys} mmHg is elevated. Cut salt intake to under 2,300mg/day. The DASH diet (fruits, vegetables, low-fat dairy) is proven to lower BP.'})
        else:
            recs.append({'category':'❤️ Blood Pressure — Good', 'color':'green',
                         'tip': f'Your BP ({bp_sys}/{bp_sys if not bp_sys else str(bp_sys)}) is in a healthy range. Keep up the good work with a low-sodium balanced diet.'})

    # Exercise — only if exercise was logged
    if exercise is not None:
        if exercise == 0:
            recs.append({'category':'🏃 Exercise — Start Today', 'color':'red',
                         'tip': 'You logged zero exercise today. Even a 15-minute walk significantly improves heart health, blood sugar, and mood. Start small and build up.'})
        elif exercise < 20:
            recs.append({'category':'🏃 Exercise — Increase', 'color':'orange',
                         'tip': f'You exercised {exercise} minutes today. The WHO recommends 30+ minutes daily. Try adding a brisk walk or short workout to reach the target.'})
        elif exercise < 30:
            recs.append({'category':'🏃 Exercise — Almost There', 'color':'orange',
                         'tip': f'{exercise} minutes is good — just a bit more to hit the 30-minute daily target. Keep it up!'})
        else:
            recs.append({'category':'🏋️ Exercise — Excellent', 'color':'green',
                         'tip': f'Great job! {exercise} minutes of exercise today. Consider mixing cardio with strength training 2-3x/week for maximum health benefits.'})

    # Sleep — only if sleep was logged
    if sleep is not None:
        if sleep < 5:
            recs.append({'category':'😴 Sleep — Critical', 'color':'red',
                         'tip': f'Only {sleep} hours of sleep is severely low. Chronic sleep deprivation raises BP, blood sugar, and stress hormones. Aim for 7-9 hours urgently.'})
        elif sleep < 7:
            recs.append({'category':'😴 Sleep — Improve', 'color':'orange',
                         'tip': f'{sleep} hours is below the 7-9 hour recommendation. Try setting a fixed bedtime, avoiding screens 1 hour before bed, and keeping your room dark and cool.'})
        elif sleep <= 9:
            recs.append({'category':'😴 Sleep — Perfect', 'color':'green',
                         'tip': f'Excellent! {sleep} hours is in the ideal 7-9 hour range. Consistent quality sleep reduces disease risk and improves mood and focus.'})
        else:
            recs.append({'category':'😴 Sleep — Too Much', 'color':'orange',
                         'tip': f'{sleep} hours may be excessive. Oversleeping is linked to fatigue and health issues. Aim to keep sleep in the 7-9 hour range.'})

    # Stress — only if stress was logged
    if stress is not None:
        if stress >= 8:
            recs.append({'category':'🧘 Stress — Critical', 'color':'red',
                         'tip': f'Stress level {stress}/10 is critically high. Chronic high stress damages the heart and immune system. Try 10 min deep breathing, a walk, or talking to someone today.'})
            recs.append({'category':'🤝 Social Support', 'color':'red',
                         'tip': 'High stress often comes from isolation. Reach out to a friend or family member today — social connection is one of the most powerful stress reducers.'})
        elif stress >= 6:
            recs.append({'category':'🧘 Stress — High', 'color':'orange',
                         'tip': f'Stress level {stress}/10 is above average. Try 5-10 minutes of meditation or deep breathing daily. Apps like Headspace or Calm can help build this habit.'})
        elif stress >= 4:
            recs.append({'category':'🧘 Stress — Moderate', 'color':'orange',
                         'tip': f'Stress level {stress}/10 is moderate. Keep managing it with regular exercise, adequate sleep, and taking breaks during work.'})
        else:
            recs.append({'category':'😌 Stress — Low', 'color':'green',
                         'tip': f'Great stress management! Level {stress}/10 is healthy. Keep up whatever you are doing — sleep, exercise and social connection all contribute.'})

    # Mood — only if mood was logged
    if mood is not None:
        if mood <= 3:
            recs.append({'category':'💙 Mood — Low', 'color':'red',
                         'tip': f'Mood score {mood}/10 is very low. Consider going outside for sunlight, doing something you enjoy, or talking to someone you trust. If this persists, speak to a professional.'})
        elif mood <= 5:
            recs.append({'category':'💛 Mood — Below Average', 'color':'orange',
                         'tip': f'Mood {mood}/10 is below average. Physical activity, good sleep, and social connection are the three best natural mood boosters.'})
        elif mood >= 8:
            recs.append({'category':'😄 Mood — Excellent', 'color':'green',
                         'tip': f'Mood score {mood}/10 is great! Positive mood is strongly linked to better physical health outcomes. Keep up the habits that are working for you.'})

    # Weight — only if weight was logged
    if weight is not None:
        bmi_note = ''
        if weight > 100:
            bmi_note = f'Weight {weight}kg is high. Consider a calorie-controlled diet and regular exercise. Even a 5-10% weight reduction significantly reduces diabetes and heart disease risk.'
        elif weight < 45:
            bmi_note = f'Weight {weight}kg may be underweight. Ensure you are eating enough calories and nutrients. Consider consulting a nutritionist.'
        if bmi_note:
            recs.append({'category':'⚖️ Weight', 'color':'orange', 'tip': bmi_note})

    if not recs:
        recs.append({'category':'✅ All Good', 'color':'green',
                     'tip': 'Your logged health values are all within healthy ranges. Keep up your current lifestyle — consistency is the key to long-term health.'})

    return recs


# Auto-train on import if models don't exist
if not os.path.exists(os.path.join(MODEL_DIR, 'diabetes_lr.pkl')):
    try:
        train_models()
    except Exception as e:
        print(f"Model training deferred: {e}")
