import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import HealthEntry
from app.ml_engine import predict_risks
from datetime import datetime, timedelta

charts = Blueprint('charts', __name__)


def _get_entries(days=30):
    since = datetime.utcnow() - timedelta(days=days)
    return HealthEntry.query\
        .filter_by(user_id=current_user.id)\
        .filter(HealthEntry.timestamp >= since)\
        .order_by(HealthEntry.timestamp.asc()).all()


def _entries_to_series(entries):
    """Convert entries list into per-metric time series dicts."""
    series = {
        'dates':    [],
        'weight':   [], 'systolic':  [], 'diastolic': [],
        'sugar':    [], 'sleep':     [], 'exercise':  [],
        'mood':     [], 'stress':    [],
    }
    for e in entries:
        series['dates'].append(e.timestamp.strftime('%b %d'))
        series['weight'].append(e.weight)
        series['systolic'].append(e.systolic_bp)
        series['diastolic'].append(e.diastolic_bp)
        series['sugar'].append(e.sugar_level)
        series['sleep'].append(e.sleep_hours)
        series['exercise'].append(e.exercise_minutes)
        series['mood'].append(e.mood)
        series['stress'].append(e.stress_level)
    return series


@charts.route('/trends')
@login_required
def trends():
    period = request.args.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    all_entries = HealthEntry.query\
        .filter_by(user_id=current_user.id)\
        .order_by(HealthEntry.timestamp.desc()).all()

    total = len(all_entries)
    entries = _get_entries(days)

    # Summary stats for the period
    def avg(lst):
        vals = [v for v in lst if v is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    series = _entries_to_series(entries)
    stats = {
        'avg_weight':   avg(series['weight']),
        'avg_systolic': avg(series['systolic']),
        'avg_diastolic':avg(series['diastolic']),
        'avg_sugar':    avg(series['sugar']),
        'avg_sleep':    avg(series['sleep']),
        'avg_exercise': avg(series['exercise']),
        'avg_mood':     avg(series['mood']),
        'avg_stress':   avg(series['stress']),
        'entry_count':  len(entries),
    }

    # Trend direction (last 2 entries vs first 2)
    def trend_dir(lst):
        vals = [v for v in lst if v is not None]
        if len(vals) < 2: return 'stable'
        return 'up' if vals[-1] > vals[0] else ('down' if vals[-1] < vals[0] else 'stable')

    trends_dir = {
        'weight':   trend_dir(series['weight']),
        'sugar':    trend_dir(series['sugar']),
        'systolic': trend_dir(series['systolic']),
        'sleep':    trend_dir(series['sleep']),
        'exercise': trend_dir(series['exercise']),
        'stress':   trend_dir(series['stress']),
    }

    return render_template('charts/trends.html',
                           series=series,
                           stats=stats,
                           trends_dir=trends_dir,
                           period=days,
                           total=total)


@charts.route('/api/chart-data')
@login_required
def chart_data():
    """JSON endpoint for dynamic chart updates."""
    period = request.args.get('period', '30', type=int)
    entries = _get_entries(period)
    series  = _entries_to_series(entries)
    return jsonify(series)
