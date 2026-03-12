"""
SHMS Gemini AI Engine
=====================
Replaces fake ML predictions with real Google Gemini AI analysis.
Sends actual health values to Gemini and gets medically accurate results.
"""

import json
import urllib.request
import urllib.error
import os

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyBVXxW7vFGFiQxzUSINOqNzemR6Lhusn34')
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"


def _call_gemini(prompt):
    """Call Gemini API and return text response."""
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1500,
        }
    }).encode('utf-8')

    req = urllib.request.Request(
        GEMINI_URL,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Gemini API HTTP error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def _safe_json(text):
    """Safely extract JSON from Gemini response."""
    if not text:
        return None
    # Strip markdown code blocks if present
    text = text.strip()
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0].strip()
    elif '```' in text:
        text = text.split('```')[1].split('```')[0].strip()
    try:
        return json.loads(text)
    except Exception as e:
        print(f"JSON parse error: {e}\nText: {text[:200]}")
        return None


def predict_risks(entry, user_age=35):
    """
    Use Gemini to predict health risks based on actual logged values.
    Returns same format as old ml_engine for compatibility.
    """

    def g(key):
        if hasattr(entry, key):
            val = getattr(entry, key)
            return val
        if isinstance(entry, dict):
            return entry.get(key)
        return None

    # Build health data summary
    fields = {
        'weight_kg':        g('weight'),
        'systolic_bp':      g('systolic_bp'),
        'diastolic_bp':     g('diastolic_bp'),
        'blood_sugar_mgdl': g('sugar_level'),
        'sleep_hours':      g('sleep_hours'),
        'exercise_minutes': g('exercise_minutes'),
        'mood_score_1_10':  g('mood'),
        'stress_level_1_10':g('stress_level'),
        'age':              user_age,
    }

    # Only include fields that were actually logged
    logged = {k: v for k, v in fields.items() if v is not None}

    if not logged:
        return _default_risks()

    prompt = f"""You are a medical AI assistant. Analyze these health metrics and provide risk assessments.

Patient health data:
{json.dumps(logged, indent=2)}

Based on established medical guidelines (WHO, AHA, ADA), provide risk assessments as a JSON object.
Use ONLY the data provided. Do not assume missing values.

Return ONLY this exact JSON format with no other text:
{{
  "diabetes": {{
    "probability": <integer 0-100>,
    "level": "<Low|Moderate|High>",
    "color": "<success|warning|danger>",
    "reason": "<one sentence explaining the score based on the actual values>"
  }},
  "hypertension": {{
    "probability": <integer 0-100>,
    "level": "<Low|Moderate|High>",
    "color": "<success|warning|danger>",
    "reason": "<one sentence explaining the score based on the actual values>"
  }},
  "stress": {{
    "probability": <integer 0-100>,
    "level": "<Low|Moderate|High>",
    "color": "<success|warning|danger>",
    "reason": "<one sentence explaining the score based on the actual values>"
  }}
}}

Medical guidelines to follow:
- Diabetes: fasting sugar >126 mg/dL = diabetic, 100-125 = pre-diabetic, <100 = normal
- Hypertension: systolic >140 = stage 2, 130-139 = stage 1, 120-129 = elevated, <120 = normal
- Stress: use stress_level score, sleep hours, and mood score
- If a metric is not provided, base the risk on available related metrics only
- probability must reflect actual medical risk, not just be a guess"""

    text = _call_gemini(prompt)
    data = _safe_json(text)

    if not data:
        return _default_risks()

    results = {}
    for risk in ['diabetes', 'hypertension', 'stress']:
        r = data.get(risk, {})
        prob = int(r.get('probability', 20))
        level = r.get('level', 'Low')
        color = r.get('color', 'success')
        results[risk] = {
            'probability': prob,
            'level':       level,
            'color':       color,
            'reason':      r.get('reason', ''),
        }

    # Overall weighted score
    overall = round(
        results['diabetes']['probability']     * 0.35 +
        results['hypertension']['probability'] * 0.40 +
        results['stress']['probability']       * 0.25,
        1
    )
    if overall >= 65:
        overall_level, overall_color = 'High Risk',     'danger'
    elif overall >= 35:
        overall_level, overall_color = 'Moderate Risk', 'warning'
    else:
        overall_level, overall_color = 'Low Risk',      'success'

    results['overall'] = {
        'score': overall,
        'level': overall_level,
        'color': overall_color,
    }
    return results


def get_alerts(entry):
    """Generate alerts based on actual health values using medical thresholds."""
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
        alerts.append({'type': 'danger', 'icon': '🚨', 'title': 'Hypertensive Range',
                       'msg': f'Systolic BP {bp_sys} mmHg is dangerously high (Stage 2 Hypertension). Seek medical advice immediately.'})
    elif bp_sys and bp_sys >= 130:
        alerts.append({'type': 'warning', 'icon': '⚠️', 'title': 'Elevated Blood Pressure',
                       'msg': f'BP {bp_sys}/{bp_dia} mmHg is Stage 1 Hypertension. Monitor closely and reduce salt intake.'})
    elif bp_sys and bp_sys >= 120:
        alerts.append({'type': 'warning', 'icon': '⚡', 'title': 'Elevated BP',
                       'msg': f'BP {bp_sys} mmHg is above normal (120-129 = elevated range). Lifestyle changes recommended.'})

    if sugar and sugar >= 200:
        alerts.append({'type': 'danger', 'icon': '🚨', 'title': 'Critical Blood Sugar',
                       'msg': f'Sugar {sugar} mg/dL is critically high. Consult a doctor immediately.'})
    elif sugar and sugar >= 126:
        alerts.append({'type': 'danger', 'icon': '🔴', 'title': 'Diabetic Range Sugar',
                       'msg': f'Fasting sugar {sugar} mg/dL is in the diabetic range (≥126). Medical evaluation needed.'})
    elif sugar and sugar >= 100:
        alerts.append({'type': 'warning', 'icon': '⚡', 'title': 'Pre-diabetic Sugar',
                       'msg': f'Sugar {sugar} mg/dL is in the pre-diabetic range (100-125). Diet changes strongly advised.'})

    if sleep and sleep < 5:
        alerts.append({'type': 'danger', 'icon': '😴', 'title': 'Severe Sleep Deprivation',
                       'msg': f'Only {sleep} hours of sleep is critically low. Chronic deprivation raises BP and blood sugar.'})
    elif sleep and sleep < 6:
        alerts.append({'type': 'warning', 'icon': '⚠️', 'title': 'Insufficient Sleep',
                       'msg': f'{sleep} hours of sleep is below the recommended 7-9 hours minimum.'})

    if stress and stress >= 8:
        alerts.append({'type': 'danger', 'icon': '🧠', 'title': 'Critical Stress Level',
                       'msg': f'Stress level {stress}/10 is critically high. This directly raises blood pressure and blood sugar.'})
    elif stress and stress >= 6:
        alerts.append({'type': 'warning', 'icon': '⚠️', 'title': 'High Stress',
                       'msg': f'Stress level {stress}/10 is above normal. Chronic stress is linked to heart disease and diabetes.'})

    if mood and mood <= 3:
        alerts.append({'type': 'warning', 'icon': '💙', 'title': 'Very Low Mood',
                       'msg': f'Mood score {mood}/10 is very low. Consider speaking to someone you trust or a mental health professional.'})

    if exercise == 0:
        alerts.append({'type': 'warning', 'icon': '🏃', 'title': 'No Exercise Today',
                       'msg': 'No exercise logged today. Even a 15-minute walk improves heart health and blood sugar regulation.'})

    return alerts


def get_recommendations(entry, risks):
    """Use Gemini to generate truly personalized recommendations."""

    def g(key):
        if hasattr(entry, key): return getattr(entry, key)
        if isinstance(entry, dict): return entry.get(key)
        return None

    fields = {
        'weight_kg':         g('weight'),
        'systolic_bp':       g('systolic_bp'),
        'diastolic_bp':      g('diastolic_bp'),
        'blood_sugar_mgdl':  g('sugar_level'),
        'sleep_hours':       g('sleep_hours'),
        'exercise_minutes':  g('exercise_minutes'),
        'mood_score_1_10':   g('mood'),
        'stress_level_1_10': g('stress_level'),
    }
    logged = {k: v for k, v in fields.items() if v is not None}

    if not logged:
        return [{'category': '📋 Log More Data', 'color': 'blue',
                 'tip': 'Fill in more health fields to get personalized AI recommendations tailored to your actual data.'}]

    risk_summary = {
        'diabetes_risk':     f"{risks.get('diabetes', {}).get('probability', 0)}% ({risks.get('diabetes', {}).get('level', 'Unknown')})",
        'hypertension_risk': f"{risks.get('hypertension', {}).get('probability', 0)}% ({risks.get('hypertension', {}).get('level', 'Unknown')})",
        'stress_risk':       f"{risks.get('stress', {}).get('probability', 0)}% ({risks.get('stress', {}).get('level', 'Unknown')})",
    }

    prompt = f"""You are a medical AI assistant providing personalized health recommendations.

Patient's logged health data today:
{json.dumps(logged, indent=2)}

AI-calculated risk scores:
{json.dumps(risk_summary, indent=2)}

Generate specific, actionable health recommendations based ONLY on the values above.
Each recommendation must directly reference the patient's actual numbers.

Return ONLY a JSON array with 4-6 recommendations in this exact format:
[
  {{
    "category": "<icon + category name, e.g. '🥗 Diet' or '😴 Sleep' or '🏃 Exercise' or '🧘 Stress' or '❤️ Blood Pressure' or '🩸 Blood Sugar' or '⚖️ Weight' or '💛 Mood'>",
    "color": "<green|orange|red|blue|purple>",
    "tip": "<specific advice that mentions the patient's actual value and what they should do>"
  }}
]

Rules:
- Only give recommendations for metrics that were actually logged
- Reference the exact numbers (e.g. "Your sugar of 140 mg/dL...")
- Be specific and actionable, not generic
- Use medical guidelines (WHO, AHA, ADA) as basis
- Tone should be supportive and clear
- Return ONLY the JSON array, no other text"""

    text = _call_gemini(prompt)
    data = _safe_json(text)

    if not data or not isinstance(data, list):
        return _fallback_recommendations(logged, risks)

    recs = []
    for item in data:
        if isinstance(item, dict) and 'category' in item and 'tip' in item:
            recs.append({
                'category': item.get('category', '💡 Tip'),
                'color':    item.get('color', 'blue'),
                'tip':      item.get('tip', ''),
            })

    return recs if recs else _fallback_recommendations(logged, risks)


def _fallback_recommendations(logged, risks):
    """Fallback if Gemini fails — still better than before."""
    recs = []
    sugar    = logged.get('blood_sugar_mgdl')
    bp_sys   = logged.get('systolic_bp')
    sleep    = logged.get('sleep_hours')
    exercise = logged.get('exercise_minutes')
    stress   = logged.get('stress_level_1_10')
    mood     = logged.get('mood_score_1_10')

    if sugar:
        if sugar >= 126:
            recs.append({'category': '🩸 Blood Sugar', 'color': 'red',
                         'tip': f'Sugar {sugar} mg/dL is in diabetic range. Cut all refined carbs and consult a doctor.'})
        elif sugar >= 100:
            recs.append({'category': '🩸 Blood Sugar', 'color': 'orange',
                         'tip': f'Sugar {sugar} mg/dL is pre-diabetic. Reduce sweets and increase fiber intake.'})
        else:
            recs.append({'category': '🩸 Blood Sugar', 'color': 'green',
                         'tip': f'Sugar {sugar} mg/dL is healthy. Keep maintaining a balanced diet.'})

    if bp_sys:
        if bp_sys >= 130:
            recs.append({'category': '❤️ Blood Pressure', 'color': 'red',
                         'tip': f'BP {bp_sys} mmHg is high. Reduce salt, avoid processed food, exercise regularly.'})
        else:
            recs.append({'category': '❤️ Blood Pressure', 'color': 'green',
                         'tip': f'BP {bp_sys} mmHg is healthy. Keep it up with regular exercise and low sodium diet.'})

    if sleep:
        if sleep < 7:
            recs.append({'category': '😴 Sleep', 'color': 'orange',
                         'tip': f'Only {sleep} hours sleep. Set a fixed bedtime and avoid screens 1 hour before bed.'})
        else:
            recs.append({'category': '😴 Sleep', 'color': 'green',
                         'tip': f'{sleep} hours sleep is great. Maintain this consistent schedule.'})

    if exercise is not None:
        if exercise < 30:
            recs.append({'category': '🏃 Exercise', 'color': 'orange',
                         'tip': f'Only {exercise} min exercise today. Aim for 30+ minutes of moderate activity daily.'})
        else:
            recs.append({'category': '🏃 Exercise', 'color': 'green',
                         'tip': f'Great job with {exercise} minutes of exercise today!'})

    return recs if recs else [{'category': '✅ Looking Good', 'color': 'green',
                                'tip': 'Your logged values look healthy. Keep up your current lifestyle!'}]


def _default_risks():
    """Return neutral risks when no data is available."""
    return {
        'diabetes':     {'probability': 0, 'level': 'Unknown', 'color': 'success', 'reason': 'No data logged'},
        'hypertension': {'probability': 0, 'level': 'Unknown', 'color': 'success', 'reason': 'No data logged'},
        'stress':       {'probability': 0, 'level': 'Unknown', 'color': 'success', 'reason': 'No data logged'},
        'overall':      {'score': 0, 'level': 'No Data', 'color': 'success'},
    }
