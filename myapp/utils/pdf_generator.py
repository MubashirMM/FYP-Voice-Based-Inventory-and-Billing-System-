from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def generate_sales_pdf(report_id, item_name, data, chart_bytes, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
     
    # Title
    elements.append(Paragraph(f"{item_name} کی رپورٹ (ID: {report_id})"))

    # Table
    table_data = [["تاریخ", "مقدار"]]
    for row in data:
        urdu_date = row["date"].strftime("%d %B").replace("January","جنوری").replace("February","فروری")
        table_data.append([urdu_date, row["qty"]])
    table = Table(table_data)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.grey)]))
    elements.append(table)

    # Chart
    img = Image(io.BytesIO(chart_bytes))
    img._restrictSize(400, 200)
    elements.append(img)

    doc.build(elements)
    return file_path
