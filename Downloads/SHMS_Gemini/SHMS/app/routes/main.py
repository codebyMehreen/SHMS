import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import HealthEntry
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@main.route('/dashboard')
@login_required
def dashboard():
    all_entries = HealthEntry.query\
                    .filter_by(user_id=current_user.id)\
                    .order_by(HealthEntry.timestamp.desc()).all()

    recent = all_entries[:5]
    latest = all_entries[0] if all_entries else None
    total  = len(all_entries)

    # Week streak — how many of last 7 days had an entry
    today   = datetime.utcnow().date()
    week_dates = [(today - timedelta(days=i)) for i in range(7)]
    entry_dates = set(e.timestamp.date() for e in all_entries)
    streak = sum(1 for d in week_dates if d in entry_dates)

    return render_template('main/dashboard.html',
                           entries=recent,
                           latest=latest,
                           total=total,
                           streak=streak)
