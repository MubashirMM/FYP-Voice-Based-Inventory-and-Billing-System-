import os
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import arabic_reshaper
from bidi.algorithm import get_display
import plotly.express as px
import plotly.io as pio 


# ======================================================
# LOAD FONT (Arabic/Urdu supporting font)
# ======================================================
# Replace with a font that supports Arabic script
font_path = r"C:\FYP\Backend\fast-api\myapp\fonts\NotoSansArabic-Regular.ttf"

if not os.path.exists(font_path):
    raise Exception("Font file not found!")

urdu_font = fm.FontProperties(fname=font_path)

# ======================================================
# HELPER: reshape + bidi for Urdu text
# ======================================================
def urdu_text(text: str) -> str:
    reshaped = arabic_reshaper.reshape(text)   # connect letters
    bidi_text = get_display(reshaped)          # apply RTL direction
    return bidi_text

# ======================================================
# GENERATE CHARTS
# ======================================================
def generate_charts(item_name: str, sales: list, charts_base_dir="charts"):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]

    charts_dir = os.path.join(
        charts_base_dir,
        f"{item_name}_{timestamp}_{unique_id}"
    )
    os.makedirs(charts_dir, exist_ok=True)

    dates = [s.sale_date for s in sales]
    quantities = [s.quantity_sold for s in sales]

    # ================= LINE =================
    plt.figure(figsize=(8, 4))
    plt.plot(dates, quantities, marker="o")

    ax = plt.gca()
    ax.set_title(urdu_text("وقت کے ساتھ فروخت کا رجحان"), fontproperties=urdu_font)
    ax.set_xlabel(urdu_text("تاریخ"), fontproperties=urdu_font)
    ax.set_ylabel(urdu_text("فروخت کی مقدار"), fontproperties=urdu_font)

    line_path = os.path.join(charts_dir, "sales_trend.png")
    plt.tight_layout()
    plt.savefig(line_path, dpi=300)
    plt.close()

    # ================= BAR =================
    plt.figure(figsize=(8, 4))
    plt.bar(dates, quantities)

    ax = plt.gca()
    ax.set_title(urdu_text("روزانہ فروخت"), fontproperties=urdu_font)
    ax.set_xlabel(urdu_text("تاریخ"), fontproperties=urdu_font)
    ax.set_ylabel(urdu_text("فروخت کی مقدار"), fontproperties=urdu_font)

    bar_path = os.path.join(charts_dir, "sales_by_day.png")
    plt.tight_layout()
    plt.savefig(bar_path, dpi=300)
    plt.close()

    # ================= PIE =================
    plt.figure(figsize=(6, 6))
    plt.pie(
        quantities,
        labels=[urdu_text(str(d)) for d in dates],
        autopct="%1.1f%%",
        textprops={'fontproperties': urdu_font}
    )

    ax = plt.gca()
    ax.set_title(urdu_text("مصنوعات کا حصہ"), fontproperties=urdu_font)

    pie_path = os.path.join(charts_dir, "item_contribution.png")
    plt.tight_layout()
    plt.savefig(pie_path, dpi=300)
    plt.close()

    # ================= AREA =================
    plt.figure(figsize=(8, 4))
    plt.stackplot(dates, quantities, labels=[urdu_text("فروخت")])

    ax = plt.gca()
    ax.set_title(urdu_text("کل فروخت میں اضافہ"), fontproperties=urdu_font)
    ax.set_xlabel(urdu_text("تاریخ"), fontproperties=urdu_font)
    ax.set_ylabel(urdu_text("فروخت کی مقدار"), fontproperties=urdu_font)

    ax.legend(prop=urdu_font)

    area_path = os.path.join(charts_dir, "cumulative_growth.png")
    plt.tight_layout()
    plt.savefig(area_path, dpi=300)
    plt.close()

    return {
        "line_chart": line_path,
        "bar_chart": bar_path,
        "pie_chart": pie_path,
        "area_chart": area_path
    }

def generate_interactive_charts(item_name: str, sales: list):
    dates = [s.sale_date for s in sales]
    quantities = [s.quantity_sold for s in sales]

    # Line chart
    fig_line = px.line(x=dates, y=quantities,
                       title=f"{item_name} وقت کے ساتھ فروخت کا رجحان",
                       labels={"x": "تاریخ", "y": "فروخت کی مقدار"})
    # Bar chart
    fig_bar = px.bar(x=dates, y=quantities,
                     title=f"{item_name} روزانہ فروخت",
                     labels={"x": "تاریخ", "y": "فروخت کی مقدار"})

    return {
        "line_chart": pio.to_json(fig_line),
        "bar_chart": pio.to_json(fig_bar)
    }
