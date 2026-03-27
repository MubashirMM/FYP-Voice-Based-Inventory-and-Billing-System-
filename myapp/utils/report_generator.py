import os
from collections import defaultdict
from datetime import datetime
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

BASE_DIR = "reports_storage" 


async def generate_report_files(report_id, sales):

    folder = f"{BASE_DIR}/report_{report_id}"
    os.makedirs(folder, exist_ok=True)

    # =====================
    # KPI
    # =====================
    total_qty = sum(s.quantity_sold for s in sales)
    total_revenue = sum(s.quantity_sold * float(s.item.unit_price) for s in sales)

    item_sales = defaultdict(float)
    for s in sales:
        item_sales[s.item.item_name] += s.quantity_sold

    top_5 = sorted(item_sales.items(), key=lambda x: x[1], reverse=True)[:5]

    # =====================
    # EXCEL
    # =====================
    excel_path = f"{folder}/report.xlsx"

    wb = Workbook()
    ws = wb.active

    ws.append(["آئٹم", "مقدار", "قیمت", "کل"])

    for s in sales:
        ws.append([
            s.item.item_name,
            s.quantity_sold,
            float(s.item.unit_price),
            s.quantity_sold * float(s.item.unit_price)
        ])

    wb.save(excel_path)

    # =====================
    # PDF DASHBOARD
    # =====================
    pdf_path = f"{folder}/dashboard.pdf"

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_path)

    elements = []

    elements.append(Paragraph("📊 فروخت ڈیش بورڈ", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"کل فروخت: {total_qty}", styles["Normal"]))
    elements.append(Paragraph(f"کل آمدنی: {total_revenue}", styles["Normal"]))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph("📌 ٹاپ 5 آئٹمز:", styles["Heading2"]))

    for item, qty in top_5:
        elements.append(Paragraph(f"{item} → {qty}", styles["Normal"]))

    elements.append(Spacer(1, 10))

    # Urdu Analysis
    if top_5:
        elements.append(Paragraph(
            f"سب سے زیادہ فروخت ہونے والا آئٹم '{top_5[0][0]}' ہے۔",
            styles["Normal"]
        ))

    doc.build(elements)

    return {
        "folder": folder,
        "excel": excel_path,
        "pdf": pdf_path,
        "kpi": {
            "total_sales": total_qty,
            "total_revenue": total_revenue,
            "top_5": top_5
        }
    }