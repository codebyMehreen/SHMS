import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Blueprint, render_template, Response, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import HealthEntry
from app.gemini_engine import predict_risks, get_alerts, get_recommendations
from app.pdf_generator import generate_report
from datetime import datetime

reports = Blueprint('reports', __name__)


@reports.route('/reports')
@login_required
def report_page():
    total = HealthEntry.query.filter_by(user_id=current_user.id).count()
    return render_template('reports/index.html', total=total)


@reports.route('/reports/download')
@login_required
def download_report():
    period = request.args.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)

    if days == 0:
        entries = HealthEntry.query\
            .filter_by(user_id=current_user.id)\
            .order_by(HealthEntry.timestamp.desc()).all()
        period_label = 'All Time'
    else:
        entries = HealthEntry.query\
            .filter_by(user_id=current_user.id)\
            .filter(HealthEntry.timestamp >= since)\
            .order_by(HealthEntry.timestamp.desc()).all()
        period_label = f'Last {days} Days'

    if not entries:
        flash('No health data found for the selected period. Log some entries first.', 'warning')
        return redirect(url_for('reports.report_page'))

    latest  = entries[0]
    age     = current_user.age or 35
    risks   = predict_risks(latest, user_age=age)
    alerts  = get_alerts(latest)
    recs    = get_recommendations(latest, risks)

    try:
        pdf_bytes = generate_report(
            user=current_user,
            entries=entries,
            risks_latest=risks,
            alerts=alerts,
            recs=recs,
            period_label=period_label
        )
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('reports.report_page'))

    filename = (f"SHMS_Report_{current_user.full_name.replace(' ','_')}_"
                f"{datetime.now().strftime('%Y%m%d')}.pdf")

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
