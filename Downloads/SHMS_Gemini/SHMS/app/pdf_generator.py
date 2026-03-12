"""
SHMS PDF Report Generator
=========================
Generates professional health reports using ReportLab.
Includes: summary stats, AI risk scores, data table, recommendations.
"""

import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Color Palette ──────────────────────────────────────────────────────────
C_BG       = colors.HexColor('#060d12')
C_DARK     = colors.HexColor('#0f1e28')
C_ACCENT   = colors.HexColor('#00d4aa')
C_BLUE     = colors.HexColor('#0099ff')
C_DANGER   = colors.HexColor('#ff4f6d')
C_WARN     = colors.HexColor('#ffb347')
C_TEXT     = colors.HexColor('#e8f4f0')
C_MUTED    = colors.HexColor('#6a8fa0')
C_BORDER   = colors.HexColor('#1e3444')
C_WHITE    = colors.white
C_BLACK    = colors.HexColor('#060d12')
C_GREEN_BG = colors.HexColor('#001a14')
C_ROW_ALT  = colors.HexColor('#0c1a22')


def _styles():
    base = getSampleStyleSheet()
    custom = {}

    custom['Title'] = ParagraphStyle(
        'ReportTitle', fontSize=26, fontName='Helvetica-Bold',
        textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=4
    )
    custom['Subtitle'] = ParagraphStyle(
        'Subtitle', fontSize=11, fontName='Helvetica',
        textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=2
    )
    custom['SectionHead'] = ParagraphStyle(
        'SectionHead', fontSize=13, fontName='Helvetica-Bold',
        textColor=C_ACCENT, spaceBefore=14, spaceAfter=6
    )
    custom['Body'] = ParagraphStyle(
        'Body', fontSize=9, fontName='Helvetica',
        textColor=C_MUTED, spaceAfter=4, leading=14
    )
    custom['Bold'] = ParagraphStyle(
        'Bold', fontSize=9, fontName='Helvetica-Bold',
        textColor=C_TEXT, spaceAfter=4
    )
    custom['Small'] = ParagraphStyle(
        'Small', fontSize=7.5, fontName='Helvetica',
        textColor=C_MUTED, spaceAfter=2
    )
    custom['RiskHigh'] = ParagraphStyle(
        'RiskHigh', fontSize=10, fontName='Helvetica-Bold',
        textColor=C_DANGER, alignment=TA_CENTER
    )
    custom['RiskMed'] = ParagraphStyle(
        'RiskMed', fontSize=10, fontName='Helvetica-Bold',
        textColor=C_WARN, alignment=TA_CENTER
    )
    custom['RiskLow'] = ParagraphStyle(
        'RiskLow', fontSize=10, fontName='Helvetica-Bold',
        textColor=C_ACCENT, alignment=TA_CENTER
    )
    custom['Center'] = ParagraphStyle(
        'Center', fontSize=9, fontName='Helvetica',
        textColor=C_TEXT, alignment=TA_CENTER
    )
    custom['CenterBold'] = ParagraphStyle(
        'CenterBold', fontSize=9, fontName='Helvetica-Bold',
        textColor=C_TEXT, alignment=TA_CENTER
    )
    return custom


def _risk_style(level, styles):
    if level == 'High':    return styles['RiskHigh']
    if level == 'Moderate':return styles['RiskMed']
    return styles['RiskLow']


def _risk_color(level):
    if level == 'High':    return C_DANGER
    if level == 'Moderate':return C_WARN
    return C_ACCENT


def generate_report(user, entries, risks_latest, alerts, recs, period_label='30 Days'):
    """
    Generate a PDF health report and return as bytes.
    
    Args:
        user          : User model object
        entries       : list of HealthEntry objects (newest first)
        risks_latest  : result of predict_risks() on latest entry
        alerts        : result of get_alerts() on latest entry
        recs          : result of get_recommendations() on latest entry
        period_label  : string like '30 Days' or 'All Time'
    
    Returns:
        bytes — the PDF file content
    """
    buffer = io.BytesIO()
    W, H   = A4
    margin = 18 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin,  bottomMargin=margin,
        title=f'SHMS Health Report — {user.full_name}',
        author='Smart Health Monitoring System',
    )

    S = _styles()
    story = []

    # ── HEADER BANNER ─────────────────────────────────────────────────────
    header_data = [[
        Paragraph('SHMS', ParagraphStyle('BrandBig', fontSize=28,
                  fontName='Helvetica-Bold', textColor=C_ACCENT, alignment=TA_LEFT)),
        Paragraph(f'Health Report<br/><font size="9" color="#6a8fa0">'
                  f'Generated {datetime.now().strftime("%B %d, %Y at %H:%M")}</font>',
                  ParagraphStyle('HeaderRight', fontSize=12,
                  fontName='Helvetica-Bold', textColor=C_TEXT, alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[W - 2*margin - 60*mm, 60*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), C_DARK),
        ('ROUNDEDCORNERS', [8]),
        ('TOPPADDING',  (0,0), (-1,-1), 14),
        ('BOTTOMPADDING',(0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING',(0,0), (-1,-1), 16),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    # ── PATIENT INFO ──────────────────────────────────────────────────────
    info_data = [
        [Paragraph('Patient', S['Small']), Paragraph('Period', S['Small']),
         Paragraph('Total Entries', S['Small']), Paragraph('Report Date', S['Small'])],
        [Paragraph(user.full_name, S['Bold']),
         Paragraph(period_label, S['Bold']),
         Paragraph(str(len(entries)), S['Bold']),
         Paragraph(datetime.now().strftime('%d %b %Y'), S['Bold'])],
    ]
    info_table = Table(info_data, colWidths=[(W - 2*margin)/4]*4)
    info_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), C_DARK),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('LINEBELOW',    (0,0), (-1,0),  0.5, C_BORDER),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_DARK]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # ── AI RISK SCORES ────────────────────────────────────────────────────
    story.append(Paragraph('AI Risk Assessment', S['SectionHead']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=10))

    ov = risks_latest.get('overall', {})
    ov_score = ov.get('score', 0)
    ov_level = ov.get('level', 'Unknown')
    ov_color = _risk_color(ov.get('color', 'success').replace('warning','Moderate').replace('success','Low').replace('danger','High'))

    # Overall score banner
    overall_data = [[
        Paragraph('Overall Health Risk Score', ParagraphStyle(
            'OvLabel', fontSize=10, fontName='Helvetica', textColor=C_MUTED, alignment=TA_CENTER)),
        Paragraph(f'{ov_score}%', ParagraphStyle(
            'OvScore', fontSize=28, fontName='Helvetica-Bold', textColor=ov_color, alignment=TA_CENTER)),
        Paragraph(ov_level, ParagraphStyle(
            'OvLevel', fontSize=12, fontName='Helvetica-Bold', textColor=ov_color, alignment=TA_CENTER)),
    ]]
    ov_table = Table(overall_data, colWidths=[(W-2*margin)/3]*3)
    ov_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), C_DARK),
        ('TOPPADDING',   (0,0), (-1,-1), 14),
        ('BOTTOMPADDING',(0,0), (-1,-1), 14),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('LINEAFTER',    (0,0), (1,-1),  0.5, C_BORDER),
    ]))
    story.append(ov_table)
    story.append(Spacer(1, 10))

    # 3 individual risks
    risk_items = [
        ('Diabetes Risk',     '🩸', risks_latest.get('diabetes',{})),
        ('Hypertension Risk', '❤️',  risks_latest.get('hypertension',{})),
        ('Stress Risk',       '🧠', risks_latest.get('stress',{})),
    ]
    risk_row = []
    for name, icon, r in risk_items:
        prob  = r.get('probability', 0)
        level = r.get('level', 'Unknown')
        col   = _risk_color(level)
        cell  = [
            Paragraph(name, S['Small']),
            Paragraph(f'{prob}%', ParagraphStyle(
                'RProb', fontSize=20, fontName='Helvetica-Bold',
                textColor=col, alignment=TA_CENTER)),
            Paragraph(level, ParagraphStyle(
                'RLevel', fontSize=9, fontName='Helvetica-Bold',
                textColor=col, alignment=TA_CENTER)),
        ]
        risk_row.append(cell)

    risk_table_data = [risk_row[0], risk_row[1], risk_row[2]]
    # Transpose so each risk is a column
    risk_cols = [[risk_row[i][j] for i in range(3)] for j in range(3)]
    risk_table = Table(
        [[risk_row[0][0], risk_row[1][0], risk_row[2][0]],
         [risk_row[0][1], risk_row[1][1], risk_row[2][1]],
         [risk_row[0][2], risk_row[1][2], risk_row[2][2]]],
        colWidths=[(W-2*margin)/3]*3
    )
    risk_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), C_DARK),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('LINEAFTER',    (0,0), (1,-1),  0.5, C_BORDER),
        ('LINEBELOW',    (0,0), (-1,1),  0.5, C_BORDER),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 16))

    # ── ALERTS ────────────────────────────────────────────────────────────
    if alerts:
        story.append(Paragraph('Health Alerts', S['SectionHead']))
        story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=8))
        for alert in alerts:
            col = C_DANGER if alert['type'] == 'danger' else C_WARN
            alert_data = [[
                Paragraph(f"<b>{alert['title']}</b>", ParagraphStyle(
                    'ATitle', fontSize=9, fontName='Helvetica-Bold', textColor=col)),
                Paragraph(alert['msg'], S['Body']),
            ]]
            at = Table(alert_data, colWidths=[45*mm, W-2*margin-45*mm])
            at.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,-1), C_DARK),
                ('TOPPADDING',   (0,0), (-1,-1), 8),
                ('BOTTOMPADDING',(0,0), (-1,-1), 8),
                ('LEFTPADDING',  (0,0), (-1,-1), 12),
                ('LINEBEFORE',   (0,0), (0,-1),  3, col),
                ('VALIGN',       (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(at)
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    # ── RECOMMENDATIONS ───────────────────────────────────────────────────
    if recs:
        story.append(Paragraph('Personalized Recommendations', S['SectionHead']))
        story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=8))
        for rec in recs:
            rec_data = [[
                Paragraph(rec['category'], ParagraphStyle(
                    'RecCat', fontSize=8.5, fontName='Helvetica-Bold', textColor=C_ACCENT)),
                Paragraph(rec['tip'], S['Body']),
            ]]
            rt = Table(rec_data, colWidths=[38*mm, W-2*margin-38*mm])
            rt.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,-1), C_DARK),
                ('TOPPADDING',   (0,0), (-1,-1), 7),
                ('BOTTOMPADDING',(0,0), (-1,-1), 7),
                ('LEFTPADDING',  (0,0), (-1,-1), 12),
                ('VALIGN',       (0,0), (-1,-1), 'TOP'),
                ('LINEBELOW',    (0,0), (-1,-1), 0.3, C_BORDER),
            ]))
            story.append(rt)
        story.append(Spacer(1, 12))

    # ── PAGE BREAK + DATA TABLE ───────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('Health Data Log', S['SectionHead']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=8))
    story.append(Paragraph(
        f'Showing {min(len(entries), 20)} most recent entries out of {len(entries)} total.',
        S['Body']))
    story.append(Spacer(1, 6))

    # Table headers
    col_labels = ['Date', 'Weight\n(kg)', 'BP\n(mmHg)', 'Sugar\n(mg/dL)',
                  'Sleep\n(hrs)', 'Exercise\n(min)', 'Mood', 'Stress']
    col_w = [28*mm, 18*mm, 24*mm, 22*mm, 18*mm, 22*mm, 16*mm, 16*mm]

    def fmt(val, suffix=''):
        return f'{val}{suffix}' if val is not None else '—'

    table_data = [[Paragraph(h, ParagraphStyle(
        'TH', fontSize=7.5, fontName='Helvetica-Bold',
        textColor=C_ACCENT, alignment=TA_CENTER)) for h in col_labels]]

    for e in entries[:20]:
        bp = f'{e.systolic_bp}/{e.diastolic_bp}' if e.systolic_bp else '—'
        row = [
            Paragraph(e.timestamp.strftime('%b %d, %Y'), S['Small']),
            Paragraph(fmt(e.weight), ParagraphStyle('TD', fontSize=8,
                fontName='Helvetica', textColor=C_TEXT, alignment=TA_CENTER)),
            Paragraph(bp, ParagraphStyle('TD2', fontSize=8,
                fontName='Helvetica', textColor=C_TEXT, alignment=TA_CENTER)),
            Paragraph(fmt(e.sugar_level), ParagraphStyle('TD3', fontSize=8,
                fontName='Helvetica', textColor=C_TEXT, alignment=TA_CENTER)),
            Paragraph(fmt(e.sleep_hours), ParagraphStyle('TD4', fontSize=8,
                fontName='Helvetica', textColor=C_TEXT, alignment=TA_CENTER)),
            Paragraph(fmt(e.exercise_minutes), ParagraphStyle('TD5', fontSize=8,
                fontName='Helvetica', textColor=C_TEXT, alignment=TA_CENTER)),
            Paragraph(fmt(e.mood), ParagraphStyle('TD6', fontSize=8,
                fontName='Helvetica', textColor=C_TEXT, alignment=TA_CENTER)),
            Paragraph(fmt(e.stress_level), ParagraphStyle('TD7', fontSize=8,
                fontName='Helvetica', textColor=C_TEXT, alignment=TA_CENTER)),
        ]
        table_data.append(row)

    data_table = Table(table_data, colWidths=col_w, repeatRows=1)
    row_colors = []
    for i in range(1, len(table_data)):
        bg = C_DARK if i % 2 == 0 else C_ROW_ALT
        row_colors.append(('BACKGROUND', (0, i), (-1, i), bg))

    data_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), C_DARK),
        ('LINEBELOW',    (0, 0), (-1, 0), 0.5, C_ACCENT),
        ('TOPPADDING',   (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
        ('LEFTPADDING',  (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW',    (0, 1), (-1, -1), 0.2, C_BORDER),
        *row_colors,
    ]))
    story.append(data_table)
    story.append(Spacer(1, 20))

    # ── FOOTER DISCLAIMER ─────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.3, color=C_BORDER, spaceAfter=6))
    story.append(Paragraph(
        'This report is generated by the Smart Health Monitoring System (SHMS) for informational '
        'purposes only and does not constitute medical advice. Always consult a qualified healthcare '
        'professional for diagnosis and treatment decisions.',
        S['Small']
    ))

    # ── BUILD ──────────────────────────────────────────────────────────────
    def _page_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_BG)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        # Page number
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(C_MUTED)
        canvas.drawRightString(W - margin, 10*mm,
                               f'Page {doc.page}  |  SHMS Health Report')
        canvas.restoreState()

    doc.build(story, onFirstPage=_page_bg, onLaterPages=_page_bg)
    buffer.seek(0)
    return buffer.getvalue()
