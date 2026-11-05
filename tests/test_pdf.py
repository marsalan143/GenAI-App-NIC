from io import BytesIO
from pypdf import PdfReader
from services.pdf_service import create_pdf, pitch_pack_markdown

def test_complete_plan_pdf(plan):
    pdf = create_pdf('Complete Business Plan', 'Campus Route', plan)
    reader = PdfReader(BytesIO(pdf))
    text = '\n'.join(p.extract_text() for p in reader.pages)
    assert pdf.startswith(b'%PDF') and len(reader.pages) >= 2
    assert '90-Day Launch Roadmap' in text and 'PKR 300,000' in text and 'Page 1' in text

def test_pitch_pack_missing_optional(pitch, canvas):
    markdown = pitch_pack_markdown(pitch, canvas)
    pdf = create_pdf('Startup Pitch Pack', 'Campus Route', markdown)
    text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
    assert 'Not assessed' in text and 'Not completed' in text
    assert all(k.replace('_', ' ').title() in text for k in type(canvas).model_fields)

def test_complete_pitch_pack(pitch, canvas, feasibility, questions, feedback):
    interview = [{'question': q, 'answer': 'Paid pilot evidence', 'feedback': feedback} for q in questions]
    markdown = pitch_pack_markdown(pitch, canvas, feasibility, interview)
    pdf = create_pdf('Startup Pitch Pack', 'Campus Route', markdown)
    text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
    assert '71.0/100' in text and '70.0/100' in text and 'Paid pilot evidence' in text

def test_long_table_and_escaped_text():
    markdown = '# <A&B>\n| A | B |\n|---|---|\n' + '\n'.join('| Long content ' + 'word ' * 40 + '| Value |' for _ in range(50))
    pdf = create_pdf('Long Table', 'A&B', markdown)
    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) > 2 and '<A&B>' in reader.pages[1].extract_text()
