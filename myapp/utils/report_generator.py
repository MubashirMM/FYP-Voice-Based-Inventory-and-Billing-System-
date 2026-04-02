"""
Sales Report Generator — Urdu + English PDF / Excel / CSV
=========================================================

ROOT CAUSE OF ALL RENDERING ISSUES (confirmed from PDF output):
================================================================

ReportLab is NOT an OpenType-aware renderer. It only does cmap lookup:
    codepoint  ->  glyph index  ->  draw glyph

It does NOT run GSUB/GPOS (OpenType tables that connect Arabic letters
contextually). So 'فروخت' (5 base codepoints) renders as FIVE DISCONNECTED
isolated shapes, or blank boxes when the cmap miss occurs.

THE FIX:
========
arabic_reshaper + python-bidi converts base codepoints to PRESENTATION FORMS
(U+FB50-U+FEFF) — the pre-connected, pre-ordered glyphs that ARE directly
in the font cmap. ReportLab can look them up with no GSUB needed.

Since arabic_reshaper may not be installed, this file has a BUILT-IN
PURE-PYTHON RESHAPER that does the same thing without any dependencies.
It is automatically used as fallback when arabic_reshaper is not available.

FONT PRIORITY:
  1. NotoNastaliqUrdu / NotoSansArabic (user-supplied in ./fonts/)
  2. FreeSerif (system font, Ubuntu/Debian) — has 379 Arabic pres. forms
  3. Download from Google Fonts (requires internet)
"""

import os
import re
import csv
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


# ═══════════════════════════════════════════════════════════════════
# BUILT-IN ARABIC/URDU RESHAPER — no external dependencies
# Covers all common Arabic + Urdu-specific letters
# ═══════════════════════════════════════════════════════════════════

_ARABIC_FORMS = {
    '\u0621': ('\uFE80', None,    None,    None   ),
    '\u0622': ('\uFE81', '\uFE82', None,    None   ),
    '\u0623': ('\uFE83', '\uFE84', None,    None   ),
    '\u0624': ('\uFE85', '\uFE86', None,    None   ),
    '\u0625': ('\uFE87', '\uFE88', None,    None   ),
    '\u0626': ('\uFE89', '\uFE8A', '\uFE8B', '\uFE8C'),
    '\u0627': ('\uFE8D', '\uFE8E', None,    None   ),
    '\u0628': ('\uFE8F', '\uFE90', '\uFE91', '\uFE92'),
    '\u0629': ('\uFE93', '\uFE94', None,    None   ),
    '\u062A': ('\uFE95', '\uFE96', '\uFE97', '\uFE98'),
    '\u062B': ('\uFE99', '\uFE9A', '\uFE9B', '\uFE9C'),
    '\u062C': ('\uFE9D', '\uFE9E', '\uFE9F', '\uFEA0'),
    '\u062D': ('\uFEA1', '\uFEA2', '\uFEA3', '\uFEA4'),
    '\u062E': ('\uFEA5', '\uFEA6', '\uFEA7', '\uFEA8'),
    '\u062F': ('\uFEA9', '\uFEAA', None,    None   ),
    '\u0630': ('\uFEAB', '\uFEAC', None,    None   ),
    '\u0631': ('\uFEAD', '\uFEAE', None,    None   ),
    '\u0632': ('\uFEAF', '\uFEB0', None,    None   ),
    '\u0633': ('\uFEB1', '\uFEB2', '\uFEB3', '\uFEB4'),
    '\u0634': ('\uFEB5', '\uFEB6', '\uFEB7', '\uFEB8'),
    '\u0635': ('\uFEB9', '\uFEBA', '\uFEBB', '\uFEBC'),
    '\u0636': ('\uFEBD', '\uFEBE', '\uFEBF', '\uFEC0'),
    '\u0637': ('\uFEC1', '\uFEC2', '\uFEC3', '\uFEC4'),
    '\u0638': ('\uFEC5', '\uFEC6', '\uFEC7', '\uFEC8'),
    '\u0639': ('\uFEC9', '\uFECA', '\uFECB', '\uFECC'),
    '\u063A': ('\uFECD', '\uFECE', '\uFECF', '\uFED0'),
    '\u0641': ('\uFED1', '\uFED2', '\uFED3', '\uFED4'),
    '\u0642': ('\uFED5', '\uFED6', '\uFED7', '\uFED8'),
    '\u0643': ('\uFED9', '\uFEDA', '\uFEDB', '\uFEDC'),
    '\u0644': ('\uFEDD', '\uFEDE', '\uFEDF', '\uFEE0'),
    '\u0645': ('\uFEE1', '\uFEE2', '\uFEE3', '\uFEE4'),
    '\u0646': ('\uFEE5', '\uFEE6', '\uFEE7', '\uFEE8'),
    '\u0647': ('\uFEE9', '\uFEEA', '\uFEEB', '\uFEEC'),
    '\u0648': ('\uFEED', '\uFEEE', None,    None   ),
    '\u0649': ('\uFEEF', '\uFEF0', None,    None   ),
    '\u064A': ('\uFEF1', '\uFEF2', '\uFEF3', '\uFEF4'),
    # Urdu-specific
    '\u0679': ('\uFB66', '\uFB67', '\uFB68', '\uFB69'),
    '\u067E': ('\uFB56', '\uFB57', '\uFB58', '\uFB59'),
    '\u0686': ('\uFB7A', '\uFB7B', '\uFB7C', '\uFB7D'),
    '\u0688': ('\uFB88', '\uFB89', None,    None   ),
    '\u0691': ('\uFB8C', '\uFB8D', None,    None   ),
    '\u0698': ('\uFB8A', '\uFB8B', None,    None   ),
    '\u06A9': ('\uFB8E', '\uFB8F', '\uFB90', '\uFB91'),
    '\u06AF': ('\uFB92', '\uFB93', '\uFB94', '\uFB95'),
    '\u06BA': ('\uFB9E', '\uFB9F', None,    None   ),
    '\u06BE': ('\uFBAA', '\uFBAB', '\uFBAC', '\uFBAD'),
    '\u06C1': ('\uFBA6', '\uFBA7', '\uFBA8', '\uFBA9'),
    '\u06CC': ('\uFBFC', '\uFBFD', '\uFBFE', '\uFBFF'),
    '\u06D2': ('\uFBAE', '\uFBAF', None,    None   ),
}

_NON_CONNECTORS = frozenset(
    '\u0621\u0622\u0623\u0624\u0625\u0627\u062F\u0630\u0631\u0632'
    '\u0648\u0649\u0688\u0691\u0698\u06BA\u06C1\u06D2'
)


def _is_rtl(text: str) -> bool:
    for ch in str(text):
        cp = ord(ch)
        if (0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F
                or 0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF):
            return True
    return False


def _reshape_run(chars: list) -> str:
    """Convert Arabic base codepoints to contextual presentation forms."""
    n = len(chars)
    out = []
    for i, ch in enumerate(chars):
        if ch not in _ARABIC_FORMS:
            out.append(ch)
            continue
        iso, fin, ini, med = _ARABIC_FORMS[ch]
        prev_c = (i > 0
                  and chars[i-1] in _ARABIC_FORMS
                  and chars[i-1] not in _NON_CONNECTORS
                  and _ARABIC_FORMS[chars[i-1]][2] is not None)
        next_c = (ch not in _NON_CONNECTORS
                  and ini is not None
                  and i < n-1
                  and chars[i+1] in _ARABIC_FORMS)
        if prev_c and next_c and med:
            out.append(med)
        elif prev_c and fin:
            out.append(fin)
        elif next_c and ini:
            out.append(ini)
        else:
            out.append(iso or ch)
    return ''.join(out)


def _builtin_shape(text: str) -> str:
    """Reshape + RTL-reverse without any external library."""
    t = str(text).strip()
    if not t or not _is_rtl(t):
        return t
    tokens = re.split(r'(\s+)', t)
    shaped = [_reshape_run(list(tok)) if _is_rtl(tok) else tok for tok in tokens]
    return ''.join(reversed(shaped))


# Prefer arabic_reshaper if installed; fall back to built-in
try:
    import arabic_reshaper as _ar
    from bidi.algorithm import get_display as _bidi_disp

    def _shape(text: str) -> str:
        t = str(text).strip()
        if not t or not _is_rtl(t):
            return t
        try:
            return _bidi_disp(_ar.reshape(t))
        except Exception:
            return _builtin_shape(t)

    print("[reshaper] arabic_reshaper + python-bidi active")

except ImportError:
    _shape = _builtin_shape
    print("[reshaper] built-in reshaper active (pip install arabic-reshaper python-bidi for better accuracy)")


# ═══════════════════════════════════════════════════════════════════
# FONT LOADING
# ═══════════════════════════════════════════════════════════════════
_FONT_CANDIDATES = [
    os.path.join("fonts", "NotoNastaliqUrdu-Regular.ttf"),
    os.path.join("fonts", "NotoSansArabic-Regular.ttf"),
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",     # Ubuntu/Debian
    "/usr/share/fonts/opentype/unifont/unifont.otf",
]
_FONT_DOWNLOADS = [
    ("https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/"
     "NotoNastaliqUrdu/NotoNastaliqUrdu-Regular.ttf",
     os.path.join("fonts", "NotoNastaliqUrdu-Regular.ttf")),
    ("https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/"
     "NotoSansArabic/NotoSansArabic-Regular.ttf",
     os.path.join("fonts", "NotoSansArabic-Regular.ttf")),
]


def _get_font() -> str:
    os.makedirs("fonts", exist_ok=True)
    for p in _FONT_CANDIDATES:
        if os.path.exists(p) and os.path.getsize(p) > 10_000:
            print(f"[font] using {p}")
            return p
    import urllib.request
    for url, dest in _FONT_DOWNLOADS:
        try:
            print(f"[font] downloading {url} …")
            urllib.request.urlretrieve(url, dest)
            if os.path.exists(dest) and os.path.getsize(dest) > 10_000:
                return dest
        except Exception as e:
            print(f"[font] download failed: {e}")
    raise RuntimeError(
        "No Arabic/Urdu font found.\n"
        "Run: sudo apt-get install fonts-freefont-ttf\n"
        "OR: place NotoSansArabic-Regular.ttf in ./fonts/"
    )


_TTF = _get_font()
pdfmetrics.registerFont(TTFont("UrduFont", _TTF))
URDU_FONT  = "UrduFont"
LATIN_FONT = "Helvetica"
_ufp = fm.FontProperties(fname=_TTF)
_lfp = fm.FontProperties(family="DejaVu Sans")


# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

def fmt(value) -> str:
    if value is None:
        return "0"
    try:
        n = float(value)
        return f"{int(n):,}" if n == int(n) else f"{n:,.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def get_unit(sales_list: list, item_name: str) -> str:
    for s in sales_list:
        if s["item_name"] == item_name:
            return s.get("item_unit", "-")
    return "-"


# ═══════════════════════════════════════════════════════════════════
# PDF PARAGRAPH BUILDERS
# ═══════════════════════════════════════════════════════════════════

def _U(text, size=11, align=TA_CENTER, tc=colors.black):
    """Urdu label — shaped, UrduFont."""
    return Paragraph(
        _shape(str(text)),
        ParagraphStyle("U", fontName=URDU_FONT, fontSize=size,
                       alignment=align, leading=size * 1.8, textColor=tc),
    )


def _D(text, size=11, align=TA_CENTER):
    """
    Dynamic item name/unit — Urdu OR English.
    UrduFont (FreeSerif/NotoSansArabic) covers ASCII so English renders fine.
    Shapes only if RTL.
    """
    t = str(text)
    display = _shape(t) if _is_rtl(t) else t
    return Paragraph(
        display,
        ParagraphStyle("D", fontName=URDU_FONT, fontSize=size,
                       alignment=align, leading=size * 1.8),
    )


def _N(text, size=11, align=TA_CENTER, tc=colors.black):
    """
    Numbers / Rs. strings — Helvetica ONLY.
    Prevents bidi from flipping "Rs. 300,000" to "300,000 .sR".
    Helvetica is LTR-only; ReportLab never applies bidi to it.
    """
    return Paragraph(
        str(text),
        ParagraphStyle("N", fontName=LATIN_FONT, fontSize=size,
                       alignment=align, leading=size * 1.8, textColor=tc),
    )


# ═══════════════════════════════════════════════════════════════════
# CHART COLORS
# ═══════════════════════════════════════════════════════════════════
BLUE       = "#2C7DA0"
PIE_COLORS = ["#2C7DA0", "#E76F51", "#2A9D8F", "#E9C46A", "#8338EC"]


# ═══════════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════════

def create_charts(sales_data: list, folder: str):
    if len(sales_data) < 5:
        return None
    charts = {}
    item_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0})
    for s in sales_data:
        item_sales[s["item_name"]]["quantity"] += s["quantity_sold"]
        item_sales[s["item_name"]]["revenue"]  += s["total_amount"]
    top       = sorted(item_sales.items(), key=lambda x: x[1]["quantity"], reverse=True)[:5]
    raw_names = [t[0] for t in top]
    quantities = [t[1]["quantity"] for t in top]

    # BAR CHART
    fig, ax = plt.subplots(figsize=(12, 6))
    x_labels = [_shape(n) if _is_rtl(n) else n for n in raw_names]
    ax.bar(range(len(x_labels)), quantities, color=BLUE, edgecolor="white", linewidth=1.5)
    for i, qty in enumerate(quantities):
        ax.text(i, qty + 0.3, str(int(qty)), ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=20, ha="right", fontsize=11)
    for tick, raw in zip(ax.get_xticklabels(), raw_names):
        tick.set_fontproperties(_ufp if _is_rtl(raw) else _lfp)
    ax.set_title(_shape("سب سے زیادہ فروخت ہونے والی اشیاء"), fontproperties=_ufp, fontsize=16, pad=15, fontweight="bold")
    ax.set_xlabel(_shape("آئٹم کا نام"),              fontproperties=_ufp, fontsize=12)
    ax.set_ylabel(_shape("فروخت شدہ مقدار (یونٹس)"), fontproperties=_ufp, fontsize=12)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    p = os.path.join(folder, "bar.png")
    fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig); charts["bar"] = p

    # PIE CHART — _ufp covers Urdu + ASCII so no legend boxes
    units = [get_unit(sales_data, n) for n in raw_names]
    legend_labels = []
    for name, qty, unit in zip(raw_names, quantities, units):
        n_d = _shape(name) if _is_rtl(name) else name
        u_d = _shape(unit) if _is_rtl(unit) else unit
        legend_labels.append(f"{n_d}  {int(qty)} {u_d}")
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, _, autotexts = ax.pie(
        quantities, labels=None, autopct="%1.1f%%",
        colors=PIE_COLORS[:len(top)], startangle=90, explode=[0.02]*len(top),
        textprops={"fontsize": 10, "fontweight": "bold"})
    for at in autotexts:
        at.set_color("white")
    legend = ax.legend(wedges, legend_labels, title=_shape("اشیاء کی تفصیل"),
                       loc="lower center", bbox_to_anchor=(0.5, -0.28),
                       ncol=3, fontsize=10, title_fontsize=12, prop=_ufp)
    legend.get_title().set_fontproperties(_ufp)
    ax.set_title(_shape("اشیاء کی فروخت کی تقسیم"), fontproperties=_ufp, fontsize=16, pad=15, fontweight="bold")
    fig.tight_layout()
    p = os.path.join(folder, "pie.png")
    fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig); charts["pie"] = p

    # LINE CHART
    daily = defaultdict(float)
    for s in sales_data:
        d = (s["sale_date"].strftime("%Y-%m-%d") if hasattr(s["sale_date"], "strftime") else str(s["sale_date"]))
        daily[d] += s["quantity_sold"]
    dates = sorted(daily.keys()); qtys = [daily[d] for d in dates]
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(dates, qtys, marker="o", linewidth=2.5, markersize=7, color=BLUE, label=_shape("فروخت"))
    ax.fill_between(dates, qtys, alpha=0.12, color=BLUE)
    for d, q in zip(dates, qtys):
        ax.annotate(str(int(q)), (d, q), textcoords="offset points", xytext=(0, 10), ha="center", fontsize=9, fontweight="bold")
    ax.set_title(_shape("وقت کے ساتھ فروخت کا رجحان"), fontproperties=_ufp, fontsize=16, pad=15, fontweight="bold")
    ax.set_xlabel(_shape("تاریخ"),                   fontproperties=_ufp, fontsize=12)
    ax.set_ylabel(_shape("فروخت کی مقدار (یونٹس)"), fontproperties=_ufp, fontsize=12)
    ax.set_xticks(range(len(dates))); ax.set_xticklabels(dates, rotation=45, ha="right", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.legend(prop=_ufp, loc="upper left")
    fig.tight_layout()
    p = os.path.join(folder, "line.png")
    fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig); charts["line"] = p

    return charts


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

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
            "sale_id": s.sale_id, "item_name": s.item_name,
            "quantity_sold": s.quantity_sold, "unit_price": up,
            "item_unit": s.item_unit or "-", "sale_date": s.sale_date,
            "total_amount": s.quantity_sold * up,
        })

    total_qty   = sum(s["quantity_sold"] for s in sales_list)
    total_rev   = sum(s["total_amount"]  for s in sales_list)
    total_trans = len(sales_list)
    total_items = len(unique_items)

    item_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0})
    for s in sales_list:
        item_sales[s["item_name"]]["quantity"] += s["quantity_sold"]
        item_sales[s["item_name"]]["revenue"]  += s["total_amount"]
    top_5 = sorted(item_sales.items(), key=lambda x: x[1]["quantity"], reverse=True)[:5]

    charts = create_charts(sales_list, folder)

    # EXCEL
    from openpyxl import Workbook
    from openpyxl.styles import Font as XF, Alignment as XA, PatternFill as XP
    excel_path = os.path.join(folder, "sales_report.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "تمام فروخت"
    hf = XF(bold=True, size=12, color="FFFFFF")
    hfill = XP(start_color="2C7DA0", end_color="2C7DA0", fill_type="solid")
    ha = XA(horizontal="center", vertical="center")
    headers = ["شناختی نمبر","آئٹم کا نام","مقدار","فی یونٹ قیمت","یونٹ","تاریخ","کل رقم"]
    ws.append(headers)
    for c in range(1, len(headers)+1):
        cell = ws.cell(row=1, column=c); cell.font=hf; cell.fill=hfill; cell.alignment=ha
    for s in sales_list:
        ws.append([s["sale_id"], s["item_name"], int(s["quantity_sold"]),
                   float(s["unit_price"]), s["item_unit"],
                   s["sale_date"].strftime("%Y-%m-%d"), float(s["total_amount"])])
    for col in ws.columns:
        w = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(w+2, 30)
    ws2 = wb.create_sheet("آئٹم کا خلاصہ")
    ws2.append(["آئٹم کا نام","کل فروخت مقدار","کل آمدنی"])
    for nm, d in sorted(item_sales.items(), key=lambda x: x[1]["quantity"], reverse=True):
        ws2.append([nm, int(d["quantity"]), float(d["revenue"])])
    wb.save(excel_path)

    # CSV
    csv_path = os.path.join(folder, "sales_export.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Sale ID","Item Name","Quantity","Unit Price","Unit","Date","Total Amount"])
        for s in sales_list:
            w.writerow([s["sale_id"], s["item_name"], int(s["quantity_sold"]),
                        float(s["unit_price"]), s["item_unit"],
                        s["sale_date"].strftime("%Y-%m-%d"), float(s["total_amount"])])

    # PDF
    pdf_path = os.path.join(folder, "dashboard.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            rightMargin=55, leftMargin=55, topMargin=55, bottomMargin=55)

    title_s   = ParagraphStyle("TS", fontName=URDU_FONT, fontSize=22,
                                textColor=colors.HexColor("#2C3E50"),
                                alignment=TA_CENTER, spaceAfter=20, spaceBefore=10)
    heading_s = ParagraphStyle("HS", fontName=URDU_FONT, fontSize=15,
                                textColor=colors.HexColor("#2C7DA0"),
                                alignment=TA_CENTER, spaceAfter=6, spaceBefore=12)
    desc_s    = ParagraphStyle("DS", fontName=URDU_FONT, fontSize=10,
                                textColor=colors.HexColor("#5A6B7A"),
                                alignment=TA_CENTER, spaceAfter=5, spaceBefore=2, leading=18)

    story = []
    story.append(Paragraph(_shape("فروخت ڈیش بورڈ"), title_s))
    story.append(Spacer(1, 0.1 * inch))

    # KPI table
    kpi_tbl = Table(
        [[_U("کل فروخت",size=12,tc=colors.white), _U("کل آمدنی",size=12,tc=colors.white),
          _U("کل لین دین",size=12,tc=colors.white), _U("منفرد اشیاء",size=12,tc=colors.white)],
         [_N(fmt(total_qty),size=14), _N(f"Rs. {fmt(total_rev)}",size=14),
          _N(fmt(total_trans),size=14), _N(fmt(total_items),size=14)]],
        colWidths=[1.7*inch]*4, rowHeights=[0.55*inch, 0.75*inch])
    kpi_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2C7DA0")),
        ("BACKGROUND",(0,1),(-1,1),colors.HexColor("#F0F8FF")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),1,colors.HexColor("#C8E0F0")),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 0.2 * inch))

    # Top-5 table
    story.append(Paragraph(_shape("پانچ سب سے زیادہ فروخت ہونے والی اشیاء"), heading_s))
    story.append(Paragraph(_shape("یہ جدول ان پانچ اشیاء کو ظاہر کرتا ہے جن کی سب سے زیادہ فروخت ہوئی ہے۔"), desc_s))
    story.append(Spacer(1, 0.05 * inch))

    top_rows = [[
        _U("درجہ",size=11,tc=colors.white), _U("آئٹم کا نام",size=11,tc=colors.white),
        _U("یونٹ",size=11,tc=colors.white), _U("مقدار",size=11,tc=colors.white),
        _U("کل آمدنی",size=11,tc=colors.white),
    ]]
    for rank, (name, data) in enumerate(top_5, 1):
        unit = get_unit(sales_list, name)
        top_rows.append([
            _N(str(rank),size=11), _D(name,size=11), _D(unit,size=11),
            _N(fmt(data["quantity"]),size=11), _N(f"Rs. {fmt(data['revenue'])}",size=11),
        ])

    # Explicit per-row alternating backgrounds (ROWBACKGROUNDS not valid in all RL versions)
    top_style = [
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2C7DA0")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#D0E8F5")),
    ]
    for ri in range(1, len(top_rows)):
        bg = colors.white if ri % 2 == 1 else colors.HexColor("#F5FBFF")
        top_style.append(("BACKGROUND",(0,ri),(-1,ri),bg))

    top_tbl = Table(top_rows,
                    colWidths=[0.5*inch,2.4*inch,0.75*inch,1.05*inch,1.65*inch],
                    rowHeights=0.48*inch)
    top_tbl.setStyle(TableStyle(top_style))
    story.append(top_tbl)
    story.append(Spacer(1, 0.15*inch))

    if charts:
        story.append(PageBreak())

        if "bar" in charts:
            block = [Paragraph(_shape("بار چارٹ: فروخت شدہ مقدار کا موازنہ"), heading_s)]
            for sent in [
                "یہ بار چارٹ پانچ سب سے زیادہ فروخت ہونے والی اشیاء کی مقدار دکھاتا ہے۔",
                "جتنا لمبا بار، اس آئٹم کی اتنی زیادہ فروخت ہوئی ہے۔",
                "یہ چارٹ سب سے مقبول مصنوعات کو آسانی سے پہچاننے میں مدد دیتا ہے۔",
            ]:
                block.append(Paragraph(_shape(sent), desc_s))
            block += [Image(charts["bar"],width=6.2*inch,height=3.8*inch), Spacer(1,0.3*inch)]
            story.append(KeepTogether(block))

        if "pie" in charts:
            block = [Paragraph(_shape("پائی چارٹ: فروخت میں حصہ داری"), heading_s)]
            for sent in [
                "یہ پائی چارٹ ظاہر کرتا ہے کہ ہر آئٹم کا کل فروخت میں کتنا فیصد حصہ ہے۔",
                "جتنا بڑا ٹکڑا، اس آئٹم کی فروخت اتنی زیادہ ہے۔",
                "اس چارٹ سے آپ فوری طور پر دیکھ سکتے ہیں کہ کون سی مصنوعات زیادہ بکتی ہیں۔",
            ]:
                block.append(Paragraph(_shape(sent), desc_s))
            block += [Image(charts["pie"],width=5.5*inch,height=4.8*inch), Spacer(1,0.3*inch)]
            story.append(KeepTogether(block))

        if "line" in charts:
            block = [Paragraph(_shape("لائن چارٹ: فروخت کا رجحان"), heading_s)]
            for sent in [
                "یہ لائن چارٹ وقت کے ساتھ فروخت میں تبدیلی کو ظاہر کرتا ہے۔",
                "اگر لائن بائیں سے دائیں اوپر جائے تو فروخت بڑھ رہی ہے۔",
                "اگر لائن نیچے جائے تو فروخت کم ہو رہی ہے۔",
                "برابر لائن کا مطلب ہے کہ ان تاریخوں میں فروخت میں کوئی تبدیلی نہیں آئی۔",
            ]:
                block.append(Paragraph(_shape(sent), desc_s))
            block += [Image(charts["line"],width=6.2*inch,height=3.8*inch)]
            story.append(KeepTogether(block))

    doc.build(story)

    return {
        "error": False, "folder": folder,
        "excel": excel_path, "csv": csv_path, "pdf": pdf_path, "charts": charts,
        "kpi": {
            "total_quantity": total_qty, "total_revenue": total_rev,
            "total_transactions": total_trans, "unique_items": total_items,
            "top_5_items": [(n, d["quantity"], d["revenue"]) for n, d in top_5],
        },
    }

