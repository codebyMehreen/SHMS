from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app import db
from app.models import HealthEntry
from datetime import datetime
import csv, io

health = Blueprint('health', __name__)

# ── Validation helpers ─────────────────────────────────────────
LIMITS = {
    'weight':           (10,   300,  'kg'),
    'systolic_bp':      (60,   250,  'mmHg'),
    'diastolic_bp':     (40,   150,  'mmHg'),
    'sugar_level':      (30,   600,  'mg/dL'),
    'sleep_hours':      (0,    24,   'hours'),
    'exercise_minutes': (0,    600,  'minutes'),
    'mood':             (1,    10,   '/10'),
    'stress_level':     (1,    10,   '/10'),
}

def validate_entry(form):
    errors = []
    values = {}
    for field, (lo, hi, unit) in LIMITS.items():
        raw = form.get(field, '').strip()
        if raw == '':
            values[field] = None
            continue
        try:
            val = float(raw) if '.' in raw else int(raw)
        except ValueError:
            errors.append(f'{field.replace("_"," ").title()} must be a number.')
            continue
        if not (lo <= val <= hi):
            errors.append(f'{field.replace("_"," ").title()} must be between {lo}–{hi} {unit}.')
            continue
        values[field] = val
    return errors, values


# ── Log new entry ──────────────────────────────────────────────
@health.route('/log', methods=['GET', 'POST'])
@login_required
def log_entry():
    if request.method == 'POST':
        errors, values = validate_entry(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('health/log.html', form_data=request.form)

        entry = HealthEntry(
            user_id          = current_user.id,
            weight           = values.get('weight'),
            systolic_bp      = values.get('systolic_bp'),
            diastolic_bp     = values.get('diastolic_bp'),
            sugar_level      = values.get('sugar_level'),
            sleep_hours      = values.get('sleep_hours'),
            exercise_minutes = values.get('exercise_minutes'),
            mood             = values.get('mood'),
            stress_level     = values.get('stress_level'),
            notes            = request.form.get('notes', '').strip() or None,
        )
        db.session.add(entry)
        db.session.commit()
        flash('Entry saved! Here is your AI health analysis 🤖', 'success')
        return redirect(url_for('ai.predict', entry_id=entry.id))

    return render_template('health/log.html', form_data={})


# ── View all entries ───────────────────────────────────────────
@health.route('/entries')
@login_required
def all_entries():
    page    = request.args.get('page', 1, type=int)
    entries = HealthEntry.query\
                .filter_by(user_id=current_user.id)\
                .order_by(HealthEntry.timestamp.desc())\
                .paginate(page=page, per_page=10, error_out=False)
    return render_template('health/entries.html', entries=entries)


# ── Edit entry ─────────────────────────────────────────────────
@health.route('/entries/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = HealthEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        errors, values = validate_entry(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('health/log.html', form_data=request.form, entry=entry, editing=True)

        entry.weight           = values.get('weight')
        entry.systolic_bp      = values.get('systolic_bp')
        entry.diastolic_bp     = values.get('diastolic_bp')
        entry.sugar_level      = values.get('sugar_level')
        entry.sleep_hours      = values.get('sleep_hours')
        entry.exercise_minutes = values.get('exercise_minutes')
        entry.mood             = values.get('mood')
        entry.stress_level     = values.get('stress_level')
        entry.notes            = request.form.get('notes', '').strip() or None
        db.session.commit()
        flash('Entry updated successfully.', 'success')
        return redirect(url_for('health.all_entries'))

    return render_template('health/log.html', form_data=entry.to_dict(), entry=entry, editing=True)


# ── Delete entry ───────────────────────────────────────────────
@health.route('/entries/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = HealthEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted.', 'info')
    return redirect(url_for('health.all_entries'))


# ── Export CSV ─────────────────────────────────────────────────
@health.route('/export/csv')
@login_required
def export_csv():
    entries = HealthEntry.query\
                .filter_by(user_id=current_user.id)\
                .order_by(HealthEntry.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date','Weight(kg)','Systolic BP','Diastolic BP',
                     'Sugar(mg/dL)','Sleep(hrs)','Exercise(min)','Mood(1-10)',
                     'Stress(1-10)','Notes'])
    for e in entries:
        writer.writerow([
            e.timestamp.strftime('%Y-%m-%d %H:%M'),
            e.weight, e.systolic_bp, e.diastolic_bp,
            e.sugar_level, e.sleep_hours, e.exercise_minutes,
            e.mood, e.stress_level, e.notes or ''
        ])

    output.seek(0)
    filename = f"health_data_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ── Import CSV ─────────────────────────────────────────────────
@health.route('/import/csv', methods=['POST'])
@login_required
def import_csv():
    file = request.files.get('csv_file')
    if not file or not file.filename.endswith('.csv'):
        flash('Please upload a valid .csv file.', 'danger')
        return redirect(url_for('health.all_entries'))

    stream  = io.StringIO(file.stream.read().decode('utf-8'))
    reader  = csv.DictReader(stream)
    imported, skipped = 0, 0

    for row in reader:
        try:
            def safe(key, cast=float):
                val = row.get(key, '').strip()
                return cast(val) if val else None

            entry = HealthEntry(
                user_id          = current_user.id,
                weight           = safe('Weight(kg)'),
                systolic_bp      = safe('Systolic BP', int),
                diastolic_bp     = safe('Diastolic BP', int),
                sugar_level      = safe('Sugar(mg/dL)'),
                sleep_hours      = safe('Sleep(hrs)'),
                exercise_minutes = safe('Exercise(min)', int),
                mood             = safe('Mood(1-10)', int),
                stress_level     = safe('Stress(1-10)', int),
                notes            = row.get('Notes', '').strip() or None,
                timestamp        = datetime.strptime(
                    row.get('Date','').strip(), '%Y-%m-%d %H:%M'
                ) if row.get('Date','').strip() else datetime.utcnow()
            )
            db.session.add(entry)
            imported += 1
        except Exception:
            skipped += 1
            continue

    db.session.commit()
    flash(f'Import complete: {imported} entries added, {skipped} skipped.', 'success')
    return redirect(url_for('health.all_entries'))
