from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import HealthEntry
from app.gemini_engine import predict_risks, get_alerts, get_recommendations

ai = Blueprint('ai', __name__)


@ai.route('/predict/<int:entry_id>')
@login_required
def predict(entry_id):
    entry = HealthEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()

    age   = current_user.age or 35
    risks = predict_risks(entry, user_age=age)
    alerts = get_alerts(entry)
    recs   = get_recommendations(entry, risks)

    return render_template('ai/predict.html',
                           entry=entry,
                           risks=risks,
                           alerts=alerts,
                           recs=recs)


@ai.route('/api/predict/<int:entry_id>')
@login_required
def predict_api(entry_id):
    entry = HealthEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()
    age   = current_user.age or 35
    risks = predict_risks(entry, user_age=age)
    return jsonify(risks)


@ai.route('/predict/latest')
@login_required
def predict_latest():
    entry = HealthEntry.query\
                .filter_by(user_id=current_user.id)\
                .order_by(HealthEntry.timestamp.desc())\
                .first()
    if not entry:
        from flask import redirect, url_for, flash
        flash('Log a health entry first to get your AI prediction.', 'info')
        return redirect(url_for('health.log_entry'))

    return predict(entry.id)
