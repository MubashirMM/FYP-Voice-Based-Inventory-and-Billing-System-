import os
import csv
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import arabic_reshaper
from bidi.algorithm import get_display
import urllib.request

# ═══════════════════════════════════════════════════════
# FONT SETUP
# ═══════════════════════════════════════════════════════

def download_google_font():
    fonts_dir = "fonts"
    os.makedirs(fonts_dir, exist_ok=True)
    font_path = os.path.join(fonts_dir, "NotoNastaliqUrdu-Regular.ttf")
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNastaliqUrdu/NotoNastaliqUrdu-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            return None
    return font_path

URDU_FONT_PATH = r"C:\FYP\Backend\fast-api\myapp\fonts\NotoSansArabic-Regular.ttf"
if not os.path.exists(URDU_FONT_PATH):
    downloaded = download_google_font()
    if downloaded and os.path.exists(downloaded):
        URDU_FONT_PATH = downloaded
if not os.path.exists(URDU_FONT_PATH):
    URDU_FONT_PATH = "C:/Windows/Fonts/Arial.ttf"

try:
    pdfmetrics.registerFont(TTFont('UrduFont', URDU_FONT_PATH))
    URDU_FONT = 'UrduFont'
except Exception:
    URDU_FONT = 'Helvetica'

LATIN_FONT = 'Helvetica'

urdu_mpl_prop  = fm.FontProperties(fname=URDU_FONT_PATH) if os.path.exists(URDU_FONT_PATH) else None
latin_mpl_prop = fm.FontProperties(family='DejaVu Sans')

# ═══════════════════════════════════════════════════════
# TEXT HELPERS
# ═══════════════════════════════════════════════════════

def _has_rtl(text: str) -> bool:
    for ch in str(text):
        cp = ord(ch)
        if (0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F or
                0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF):
            return True
    return False


def urdu(text: str) -> str:
    """
    Reshape + bidi for Urdu/Arabic text.
    CALL THIS ONLY ONCE per string — calling it twice breaks the shaping.
    Never call on English text or numbers.
    """
    text = str(text).strip()
    if not text or not _has_rtl(text):
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def fmt(value) -> str:
    if value is None:
        return "0"
    try:
        n = float(value)
        return f"{int(n):,}" if n == int(n) else f"{n:,.2f}".rstrip('0').rstrip('.')
    except Exception:
        return str(value)


def get_item_unit(sales_list, item_name):
    for s in sales_list:
        if s['item_name'] == item_name:
            return s.get('item_unit', 'عدد')
    return 'عدد'

# ═══════════════════════════════════════════════════════
# PDF PARAGRAPH HELPERS
# Every table cell is a Paragraph with its own font so ReportLab
# never silently applies UrduFont to Latin text (which has no Latin glyphs).
# ═══════════════════════════════════════════════════════

def _u(text, size=11, align=TA_CENTER, tc=colors.black):
    """Urdu paragraph — reshape once here, never pre-reshape before calling."""
    return Paragraph(
        urdu(str(text)),
        ParagraphStyle('_u', fontName=URDU_FONT, fontSize=size,
                       alignment=align, leading=size * 1.5, textColor=tc)
    )

def _l(text, size=11, align=TA_CENTER, tc=colors.black):
    """Latin paragraph — Helvetica, no bidi, for English names / numbers / Rs."""
    return Paragraph(
        str(text),
        ParagraphStyle('_l', fontName=LATIN_FONT, fontSize=size,
                       alignment=align, leading=size * 1.5, textColor=tc)
    )

def _auto(text, size=11, align=TA_CENTER):
    """Auto-detect script and pick the right paragraph style."""
    return _u(text, size, align) if _has_rtl(str(text)) else _l(text, size, align)

# ═══════════════════════════════════════════════════════
# CHART COLORS — distinct colors for pie, single blue for bar/line
# ═══════════════════════════════════════════════════════
BLUE          = '#2C7DA0'
PIE_COLORS    = ['#2C7DA0', '#E76F51', '#2A9D8F', '#E9C46A', '#8338EC']

# ═══════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════

def create_beautiful_charts(sales_data, folder):
    if len(sales_data) < 5:
        return None

    charts = {}
    item_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0})
    for s in sales_data:
        item_sales[s['item_name']]["quantity"] += s['quantity_sold']
        item_sales[s['item_name']]["revenue"]  += s['total_amount']

    top_items = sorted(item_sales.items(), key=lambda x: x[1]["quantity"], reverse=True)[:5]

    # ── BAR CHART — single professional blue, no shadow
    if top_items:
        fig, ax = plt.subplots(figsize=(12, 6))
        raw_names  = [i[0] for i in top_items]
        quantities = [i[1]["quantity"] for i in top_items]
        # chart label: reshape Urdu once; English passes through unchanged
        labels = [urdu(n) if _has_rtl(n) else n for n in raw_names]

        bars = ax.bar(range(len(labels)), quantities,
                      color=BLUE, edgecolor='white', linewidth=1.5)
        for bar, qty in zip(bars, quantities):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(int(qty)), ha='center', va='bottom', fontsize=11, fontweight='bold')

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=11)
        for tick, raw in zip(ax.get_xticklabels(), raw_names):
            tick.set_fontproperties(urdu_mpl_prop if (_has_rtl(raw) and urdu_mpl_prop) else latin_mpl_prop)

        ax.set_title(urdu("سب سے زیادہ فروخت ہونے والی اشیاء"),
                     fontproperties=urdu_mpl_prop, fontsize=16, pad=15, fontweight='bold')
        ax.set_xlabel(urdu("آئٹم کا نام"),              fontproperties=urdu_mpl_prop, fontsize=12)
        ax.set_ylabel(urdu("فروخت شدہ مقدار (یونٹس)"), fontproperties=urdu_mpl_prop, fontsize=12)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        path = os.path.join(folder, "top_items_bar.png")
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        charts['bar_chart'] = path

    # ── PIE CHART — distinct colors, NO shadow, simple flat circle
    if top_items:
        fig, ax = plt.subplots(figsize=(9, 7))
        raw_names  = [i[0] for i in top_items]
        quantities = [i[1]["quantity"] for i in top_items]
        units      = [get_item_unit(sales_data, n) for n in raw_names]

        # Legend labels: build as plain strings mixing Latin + Urdu carefully.
        # Units that are Urdu (e.g. بوری) need reshaping for matplotlib.
        # We do NOT mix reshaped Urdu + Latin in the same string because
        # matplotlib cannot apply per-character font inside a single Text object.
        # Solution: show item name on line 1, quantity+unit on line 2 separately.
        legend_labels = []
        for name, qty, unit in zip(raw_names, quantities, units):
            name_part = urdu(name) if _has_rtl(name) else name
            unit_part = urdu(unit) if _has_rtl(unit) else unit
            # Format: "name\nqty unit" — qty is always Latin digits
            legend_labels.append(f"{name_part}\n{int(qty)} {unit_part}")

        wedges, _, autotexts = ax.pie(
            quantities,
            labels=None,
            autopct='%1.1f%%',
            colors=PIE_COLORS[:len(top_items)],
            startangle=90,
            explode=[0.02] * len(top_items),
            shadow=False,                        # FIX: no shadow — clean flat circle
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        for at in autotexts:
            at.set_color('white')
            at.set_fontsize(10)
            at.set_fontweight('bold')

        legend = ax.legend(
            wedges, legend_labels,
            title=urdu("اشیاء کی تفصیل"),
            loc='lower center',
            bbox_to_anchor=(0.5, -0.30),
            ncol=3, fontsize=10, title_fontsize=12,
            prop=latin_mpl_prop                  # start Latin; override per entry below
        )
        # Per-entry font: Urdu item → urdu font; English item → latin font
        # The unit portion on line 2 is also handled by the same font choice
        # because matplotlib applies one font per Text object.
        # For mixed entries (English name + Urdu unit), use urdu_mpl_prop
        # so the Urdu unit renders; the English digits are present in the font too
        # (NotoSansArabic includes ASCII digits).
        for txt, (raw_name, raw_unit) in zip(legend.get_texts(), zip(raw_names, units)):
            needs_urdu_font = _has_rtl(raw_name) or _has_rtl(raw_unit)
            txt.set_fontproperties(urdu_mpl_prop if (needs_urdu_font and urdu_mpl_prop) else latin_mpl_prop)

        if urdu_mpl_prop:
            legend.get_title().set_fontproperties(urdu_mpl_prop)

        ax.set_title(urdu("اشیاء کی فروخت کی تقسیم"),
                     fontproperties=urdu_mpl_prop, fontsize=16, pad=15, fontweight='bold')
        fig.tight_layout()
        path = os.path.join(folder, "distribution_pie.png")
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        charts['pie_chart'] = path

    # ── LINE CHART — single professional blue
    if len(sales_data) >= 3:
        daily = defaultdict(float)
        for s in sales_data:
            d = s['sale_date'].strftime("%Y-%m-%d") if hasattr(s['sale_date'], 'strftime') else str(s['sale_date'])
            daily[d] += s['quantity_sold']
        dates = sorted(daily.keys())
        qtys  = [daily[d] for d in dates]

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(dates, qtys, marker='o', linewidth=2.5, markersize=7,
                color=BLUE, label=urdu("فروخت"))
        ax.fill_between(dates, qtys, alpha=0.15, color=BLUE)
        for d, q in zip(dates, qtys):
            ax.annotate(str(int(q)), (d, q), textcoords="offset points",
                        xytext=(0, 10), ha='center', fontsize=9, fontweight='bold')

        ax.set_title(urdu("وقت کے ساتھ فروخت کا رجحان"),
                     fontproperties=urdu_mpl_prop, fontsize=16, pad=15, fontweight='bold')
        ax.set_xlabel(urdu("تاریخ"),                     fontproperties=urdu_mpl_prop, fontsize=12)
        ax.set_ylabel(urdu("فروخت کی مقدار (یونٹس)"),   fontproperties=urdu_mpl_prop, fontsize=12)
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha='right', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(prop=urdu_mpl_prop if urdu_mpl_prop else latin_mpl_prop, loc='upper left')
        fig.tight_layout()
        path = os.path.join(folder, "sales_trend.png")
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        charts['line_chart'] = path

    return charts

# ═══════════════════════════════════════════════════════
# PDF PARAGRAPH STYLE FOR DESCRIPTIONS
# FIX: description paragraphs were showing line 1 below line 2 because
# ReportLab's bidi paragraph mode was reversing line order.
# Solution: split long Urdu descriptions at natural sentence boundaries
# and emit each sentence as a separate Paragraph — this prevents the
# multi-line bidi reordering bug entirely.
# ═══════════════════════════════════════════════════════

def urdu_desc(text: str, style) -> list:
    """
    Split a long Urdu description into individual sentence Paragraphs.
    This avoids ReportLab reversing the visual order of wrapped lines
    in multi-line RTL paragraphs.
    """
    # Split on Urdu sentence-ending punctuation or '۔'
    import re
    parts = re.split(r'(?<=[۔،])\s*', str(text).strip())
    paras = []
    for part in parts:
        part = part.strip()
        if part:
            paras.append(Paragraph(urdu(part), style))
    return paras if paras else [Paragraph(urdu(text), style)]

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

async def generate_report_files(report_id, sales):
    unique_items = {s.item_name for s in sales}
    if len(unique_items) < 5:
        return {"error": True,
                "message": "رپورٹ جنریٹ کرنے کے لیے کم از کم 5 مختلف اشیاء کی فروخت ضروری ہے۔"}

    folder = f"reports_storage/report_{report_id}"
    os.makedirs(folder, exist_ok=True)

    sales_list = []
    for s in sales:
        up = float(s.unit_price) if s.unit_price else 0
        sales_list.append({
            'sale_id':       s.sale_id,
            'item_name':     s.item_name,
            'quantity_sold': s.quantity_sold,
            'unit_price':    up,
            'item_unit':     s.item_unit or 'عدد',
            'sale_date':     s.sale_date,
            'total_amount':  s.quantity_sold * up,
        })

    total_quantity     = sum(s['quantity_sold'] for s in sales_list)
    total_revenue      = sum(s['total_amount']  for s in sales_list)
    total_transactions = len(sales_list)
    unique_items_count = len(unique_items)

    item_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0})
    for s in sales_list:
        item_sales[s['item_name']]["quantity"] += s['quantity_sold']
        item_sales[s['item_name']]["revenue"]  += s['total_amount']
    top_5 = sorted(item_sales.items(), key=lambda x: x[1]["quantity"], reverse=True)[:5]

    charts = create_beautiful_charts(sales_list, folder)

    # ── EXCEL
    from openpyxl import Workbook
    from openpyxl.styles import Font as XFont, Alignment as XAlign, PatternFill
    excel_path = os.path.join(folder, "sales_report.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "تمام فروخت"
    hf    = XFont(bold=True, size=12, color="FFFFFF")
    hfill = PatternFill(start_color="2C7DA0", end_color="2C7DA0", fill_type="solid")
    ha    = XAlign(horizontal="center", vertical="center")
    headers = ["شناختی نمبر","آئٹم کا نام","مقدار","فی یونٹ قیمت","یونٹ","تاریخ","کل رقم"]
    ws.append(headers)
    for c in range(1, len(headers)+1):
        cell = ws.cell(row=1, column=c); cell.font=hf; cell.fill=hfill; cell.alignment=ha
    for s in sales_list:
        ws.append([s['sale_id'], s['item_name'], int(s['quantity_sold']),
                   float(s['unit_price']), s['item_unit'],
                   s['sale_date'].strftime("%Y-%m-%d"), float(s['total_amount'])])
    for col in ws.columns:
        w = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(w+2, 30)
    ws2 = wb.create_sheet("آئٹم کا خلاصہ")
    ws2.append(["آئٹم کا نام","کل فروخت مقدار","کل آمدنی"])
    for nm, d in sorted(item_sales.items(), key=lambda x: x[1]["quantity"], reverse=True):
        ws2.append([nm, int(d["quantity"]), float(d["revenue"])])
    wb.save(excel_path)

    # ── CSV
    csv_path = os.path.join(folder, "sales_export.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["Sale ID","Item Name","Quantity","Unit Price","Unit","Date","Total Amount"])
        for s in sales_list:
            w.writerow([s['sale_id'], s['item_name'], int(s['quantity_sold']),
                        float(s['unit_price']), s['item_unit'],
                        s['sale_date'].strftime("%Y-%m-%d"), float(s['total_amount'])])

    # ── PDF
    pdf_path = os.path.join(folder, "dashboard.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            rightMargin=55, leftMargin=55, topMargin=55, bottomMargin=55)

    # ── Styles
    title_style = ParagraphStyle(
        'T', fontName=URDU_FONT, fontSize=22,
        textColor=colors.HexColor('#2C3E50'),
        alignment=TA_CENTER, spaceAfter=20, spaceBefore=10)

    heading_style = ParagraphStyle(
        'H', fontName=URDU_FONT, fontSize=15,
        textColor=colors.HexColor('#2C7DA0'),
        alignment=TA_CENTER, spaceAfter=6, spaceBefore=12)

    # FIX: description uses TA_CENTER and small leading — each sentence is its
    # own Paragraph so line-order reversal cannot happen across wrapped lines.
    desc_style = ParagraphStyle(
        'D', fontName=URDU_FONT, fontSize=10,
        textColor=colors.HexColor('#5A6B7A'),
        alignment=TA_CENTER, spaceAfter=6, spaceBefore=2,
        leading=16)

    story = []

    # Title — urdu() called ONCE here
    story.append(Paragraph(urdu("فروخت ڈیش بورڈ"), title_style))
    story.append(Spacer(1, 0.1 * inch))

    # ── KPI table
    # FIX: _u() calls urdu() internally — do NOT pre-call urdu() before _u()
    # Calling urdu() twice corrupts the shaped text (letters break apart).
    kpi_labels = [
        _u("کل فروخت",   size=12, align=TA_CENTER, tc=colors.white),
        _u("کل آمدنی",   size=12, align=TA_CENTER, tc=colors.white),
        _u("کل لین دین", size=12, align=TA_CENTER, tc=colors.white),
        _u("منفرد اشیاء",size=12, align=TA_CENTER, tc=colors.white),
    ]
    kpi_values = [
        _l(fmt(total_quantity),          size=14, align=TA_CENTER),
        _l(f"Rs. {fmt(total_revenue)}",  size=14, align=TA_CENTER),
        _l(fmt(total_transactions),      size=14, align=TA_CENTER),
        _l(fmt(unique_items_count),      size=14, align=TA_CENTER),
    ]

    kpi_tbl = Table([kpi_labels, kpi_values],
                    colWidths=[1.7*inch]*4, rowHeights=[0.55*inch, 0.75*inch])
    kpi_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C7DA0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F0F8FF')),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',       (0,0), (-1,-1), 1, colors.HexColor('#C8E0F0')),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 0.2 * inch))

    # ── Top-5 table
    # _u() and _auto() each call urdu() once internally — never pre-reshape
    story.append(Paragraph(urdu("پانچ سب سے زیادہ فروخت ہونے والی اشیاء"), heading_style))
    story.extend(urdu_desc(
        "یہ جدول ان پانچ اشیاء کو ظاہر کرتا ہے جن کی سب سے زیادہ فروخت ہوئی ہے۔",
        desc_style))
    story.append(Spacer(1, 0.05 * inch))

    header_row = [
        _u("درجہ",       size=11, tc=colors.white),
        _u("آئٹم کا نام",size=11, tc=colors.white),
        _u("یونٹ",        size=11, tc=colors.white),
        _u("مقدار",       size=11, tc=colors.white),
        _u("کل آمدنی",   size=11, tc=colors.white),
    ]
    top_rows = [header_row]
    for rank, (name, data) in enumerate(top_5, 1):
        unit = get_item_unit(sales_list, name)
        top_rows.append([
            _l(str(rank),                    size=11),
            _auto(name,                       size=11),   # English or Urdu item name
            _auto(unit,                       size=11),   # English or Urdu unit
            _l(fmt(data["quantity"]),         size=11),
            _l(f"Rs. {fmt(data['revenue'])}", size=11),
        ])

    top_tbl = Table(top_rows,
                    colWidths=[0.5*inch, 2.4*inch, 0.75*inch, 1.05*inch, 1.65*inch],
                    rowHeights=0.48*inch)
    top_tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (-1,0), colors.HexColor('#2C7DA0')),
        ('ALIGN',          (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',         (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',           (0,0), (-1,-1), 0.5, colors.HexColor('#D0E8F5')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5FBFF')]),
    ]))
    story.append(top_tbl)
    story.append(Spacer(1, 0.15 * inch))

    # ── Charts — KeepTogether keeps heading + description + image on same page
    if charts:
        story.append(PageBreak())

        if 'bar_chart' in charts:
            block = [
                Paragraph(urdu("بار چارٹ: فروخت شدہ مقدار کا موازنہ"), heading_style),
            ]
            block.extend(urdu_desc(
                "یہ بار چارٹ پانچ سب سے زیادہ فروخت ہونے والی اشیاء کی مقدار کو ظاہر کرتا ہے۔"
                " ہر بار کی اونچائی اس آئٹم کی کل فروخت شدہ مقدار کو نمایاں کرتی ہے۔",
                desc_style))
            block += [Image(charts['bar_chart'], width=6.2*inch, height=3.8*inch),
                      Spacer(1, 0.3*inch)]
            story.append(KeepTogether(block))

        if 'pie_chart' in charts:
            block = [
                Paragraph(urdu("پائی چارٹ: فروخت میں حصہ داری"), heading_style),
            ]
            block.extend(urdu_desc(
                "یہ پائی چارٹ ظاہر کرتا ہے کہ کل فروخت میں ہر آئٹم کا کتنا فیصد حصہ ہے۔"
                " اس چارٹ سے آپ آسانی سے دیکھ سکتے ہیں کہ کون سی اشیاء زیادہ فروخت ہوتی ہیں۔",
                desc_style))
            block += [Image(charts['pie_chart'], width=5.5*inch, height=4.8*inch),
                      Spacer(1, 0.3*inch)]
            story.append(KeepTogether(block))

        if 'line_chart' in charts:
            block = [
                Paragraph(urdu("لائن چارٹ: فروخت کا رجحان"), heading_style),
            ]
            block.extend(urdu_desc(
                "یہ لائن چارٹ وقت کے ساتھ فروخت کے رجحان کو ظاہر کرتا ہے۔"
                " یہ دیکھنے میں مدد کرتا ہے کہ فروخت بڑھ رہی ہے یا کم ہو رہی ہے۔",
                desc_style))
            block += [Image(charts['line_chart'], width=6.2*inch, height=3.8*inch)]
            story.append(KeepTogether(block))

    doc.build(story)

    return {
        "error": False,
        "folder": folder,
        "excel":  excel_path,
        "csv":    csv_path,
        "pdf":    pdf_path,
        "charts": charts,
        "kpi": {
            "total_quantity":     total_quantity,
            "total_revenue":      total_revenue,
            "total_transactions": total_transactions,
            "unique_items":       unique_items_count,
            "top_5_items": [(n, d["quantity"], d["revenue"]) for n, d in top_5],
        },
    }