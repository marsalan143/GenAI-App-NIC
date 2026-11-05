"""ReportLab export: escaped text, wrapped tables, repeated headers and page numbers."""
from io import BytesIO
from html import escape
import re
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from utils import WEIGHTS, LABELS, DISCLAIMER, feasibility_score, investor_score

NAVY = colors.HexColor('#0B1026')
BLUE = colors.HexColor('#2563EB')

def clean(text):
    # AI deliverables are requested in English; normalize typographic punctuation.
    return str(text).translate(str.maketrans({'\u2011': '-', '\u2013': '-', '\u2014': '-', '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2022': '-'}))

def inline(text):
    value = escape(clean(text))
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'`([^`]+)`', r'\1', value)
    return value

def create_pdf(title, startup_name, markdown):
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='VFBody', fontName='Helvetica', fontSize=10, leading=15, spaceAfter=8, textColor=NAVY, splitLongWords=True))
    styles.add(ParagraphStyle(name='VFCell', parent=styles['VFBody'], fontSize=8, leading=11, spaceAfter=0))
    styles.add(ParagraphStyle(name='VFCover', fontName='Helvetica-Bold', fontSize=32, leading=39, textColor=NAVY, spaceAfter=20))
    styles['Heading1'].textColor = BLUE
    styles['Heading2'].textColor = NAVY
    story = [Spacer(1, 80), Paragraph('NIC VENTUREFORGE AI', styles['Heading2']),
             Spacer(1, 25), Paragraph(inline(title), styles['VFCover']),
             Paragraph(inline(startup_name), styles['Heading1']), Spacer(1, 20),
             Paragraph('From Problem to Pitch-Ready Startup', styles['VFBody']),
             Paragraph('AI-generated planning document. Market, competitor and financial claims are unverified assumptions unless explicitly supported by founder evidence.', styles['VFBody']),
             Paragraph('Student assignment project. No official NIC endorsement is implied.', styles['VFBody']), PageBreak()]
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*', cell) for cell in cells):
                    rows.append(cells)
                i += 1
            if rows:
                count = max(len(row) for row in rows)
                data = [[Paragraph(inline(cell.strip()), styles['VFCell']) for cell in row + [''] * (count - len(row))] for row in rows]
                table = Table(data, colWidths=[(A4[0] - 100) / count] * count, repeatRows=1, hAlign='LEFT', splitInRow=1)
                table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DBEAFE')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#CBD5E1')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                    ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
                story.extend([table, Spacer(1, 12)])
            continue
        if line and line not in ('---', '```', '```markdown'):
            heading = re.match(r'^(#{1,6})\s+(.*)', line)
            if heading:
                story.append(Paragraph(inline(heading[2]), styles['Heading1' if len(heading[1]) == 1 else 'Heading2']))
            else:
                story.append(Paragraph(inline(line), styles['VFBody']))
        i += 1

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#CBD5E1'))
        canvas.line(50, 43, A4[0] - 50, 43)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(NAVY)
        canvas.drawString(50, 29, 'NIC VentureForge AI | Educational AI assessment')
        canvas.drawRightString(A4[0] - 50, 29, f'Page {doc.page}')
        canvas.restoreState()

    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=45, bottomMargin=60, title=clean(title), author='NIC VentureForge AI')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()

def pitch_pack_markdown(pitch, canvas, feasibility=None, interview=None, source='Original plan'):
    chunks = [f'# Investor Pitch Summary\nPlan version: {source}']
    for key, value in pitch.model_dump().items():
        chunks.append(f'## {key.replace("_", " ").title()}\n{value}')
    chunks.append('# Business Model Canvas')
    for key, values in canvas.model_dump().items():
        chunks.append(f'## {key.replace("_", " ").title()}\n' + '\n'.join('- ' + x for x in values))
    chunks.append('# Feasibility Summary (original plan)')
    if feasibility:
        chunks += [f'Overall provisional score: {feasibility_score(feasibility)}/100', DISCLAIMER,
                   '| Category | Score | Weight |\n|---|---|---|\n' + '\n'.join(f'| {LABELS[k]} | {getattr(feasibility, k).score} | {w:.0%} |' for k, w in WEIGHTS.items()), feasibility.summary]
        for key in ['strengths', 'weaknesses', 'risks', 'recommendations', 'assumptions_to_validate']:
            chunks.append(f'## {key.replace("_", " ").title()}\n' + '\n'.join('- ' + x for x in getattr(feasibility, key)))
    else:
        chunks.append('Not assessed.')
    chunks.append('# Investor Challenge Feedback (original plan)\nSimulated AI investor. Educational estimates only.')
    if interview and len(interview) == 5:
        chunks.append(f'Pitch readiness: {investor_score(interview)}/100')
        for i, item in enumerate(interview, 1):
            chunks += [f'## Question {i}: {item["question"].question}', f'Founder answer: {item["answer"]}', f'Score: {item["feedback"].score}/10']
            for key, values in item['feedback'].model_dump().items():
                if key != 'score':
                    chunks.append(f'### {key.replace("_", " ").title()}\n' + '\n'.join('- ' + x for x in values))
    else:
        chunks.append('Not completed. No final investor score is available.')
    return '\n\n'.join(chunks)
