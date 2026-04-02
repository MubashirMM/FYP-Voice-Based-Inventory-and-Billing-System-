# myapp/utils/forecast_report_charts.py
import os
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import warnings
warnings.filterwarnings('ignore')

# Font and text processing imports
import arabic_reshaper
from bidi.algorithm import get_display
import urllib.request
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ═══════════════════════════════════════════════════════════════════
# FONT SYSTEM (FULL UNICODE FONT - SUPPORTS URDU + ENGLISH)
# ALL MESSAGES IN URDU
# ═══════════════════════════════════════════════════════════════════

FONT_DIR = "fonts"
os.makedirs(FONT_DIR, exist_ok=True)

# 🔥 CRITICAL FIX: Use NotoSans-Regular.ttf (Full Unicode) instead of NotoSansArabic
UNICODE_FONT_PATH = os.path.join(FONT_DIR, "NotoSans-Regular.ttf")


def _urdu_msg(text):
    """Convert message to Urdu display format for console"""
    try:
        # Simple check for Urdu characters
        for ch in text:
            if ord(ch) >= 0x0600:
                try:
                    return get_display(arabic_reshaper.reshape(text))
                except:
                    return text
        return text
    except:
        return text


def _download_font(url, path):
    """Download font from URL to specified path"""
    try:
        print(_urdu_msg(f"📥 ڈاؤن لوڈ ہو رہا ہے: {url}"))
        urllib.request.urlretrieve(url, path)
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            print(_urdu_msg(f"✅ کامیابی سے محفوظ: {path}"))
            return True
        else:
            print(_urdu_msg(f"❌ ڈاؤن لوڈ ناکام: فائل بہت چھوٹی"))
            return False
    except Exception as e:
        print(_urdu_msg(f"❌ ڈاؤن لوڈ میں خرابی: {e}"))
        return False


def _ensure_font():
    """Ensure full Unicode font is available, download if missing"""
    
    # Check if old broken font exists and remove it
    old_font_path = os.path.join(FONT_DIR, "NotoSansArabic-Regular.ttf")
    if os.path.exists(old_font_path):
        print(_urdu_msg("🗑️ پرانا فونٹ ہٹایا جا رہا ہے (NotoSansArabic)..."))
        try:
            os.remove(old_font_path)
            print(_urdu_msg("✅ پرانا فونٹ ہٹا دیا گیا"))
        except:
            print(_urdu_msg("⚠️ پرانا فونٹ ہٹانے میں مسئلہ"))
    
    # Check and download full Unicode font
    if not os.path.exists(UNICODE_FONT_PATH):
        print(_urdu_msg("🔍 مکمل یونیکوڈ فونٹ نہیں ملا، ڈاؤن لوڈ ہو رہا ہے..."))
        # 🔥 Updated URLs for full Unicode NotoSans
        font_urls = [
            "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
            "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
            "https://cdn.jsdelivr.net/gh/googlefonts/noto-fonts@main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
        ]
        
        downloaded = False
        for url in font_urls:
            if _download_font(url, UNICODE_FONT_PATH):
                downloaded = True
                break
        
        if not downloaded:
            print(_urdu_msg("❌ فونٹ ڈاؤن لوڈ نہیں ہو سکا۔ براہ کرم انٹرنیٹ کنکشن چیک کریں۔"))
            raise RuntimeError("Font download failed")
    else:
        print(_urdu_msg(f"✅ مکمل یونیکوڈ فونٹ پہلے سے موجود: {UNICODE_FONT_PATH}"))
    
    print(_urdu_msg("✅ فونٹ کامیابی سے لوڈ ہو گیا"))
    return UNICODE_FONT_PATH


# Initialize fonts (downloads if needed)
print(_urdu_msg("🚀 فونٹ سسٹم شروع ہو رہا ہے..."))
FONT_PATH = _ensure_font()

# Register font
pdfmetrics.registerFont(TTFont("UnicodeFont", FONT_PATH))
UNICODE_FONT = "UnicodeFont"

# Setup matplotlib fonts
_unicode_mpl = matplotlib.font_manager.FontProperties(fname=FONT_PATH)

print(_urdu_msg("🎉 فونٹ سسٹم تیار ہے (اب انگلش بھی صحیح ظاہر ہو گا)"))


# ═══════════════════════════════════════════════════════════════════
# TEXT HELPERS
# ═══════════════════════════════════════════════════════════════════

def _is_rtl(text: str) -> bool:
    """Check if text contains RTL characters (Urdu/Arabic)"""
    if not text:
        return False
    for ch in str(text):
        cp = ord(ch)
        if (0x0600 <= cp <= 0x06FF or
            0x0750 <= cp <= 0x077F or
            0xFB50 <= cp <= 0xFDFF or
            0xFE70 <= cp <= 0xFEFF):
            return True
    return False


def _shape(text: str) -> str:
    """Reshape + bidi Urdu/Arabic. Call ONCE per string. No-op for Latin."""
    t = str(text).strip()
    if not t or not _is_rtl(t):
        return t
    try:
        return get_display(arabic_reshaper.reshape(t))
    except Exception:
        return t


def fmt(value) -> str:
    """Format numbers nicely"""
    if value is None:
        return "0"
    try:
        n = float(value)
        return f"{int(n):,}" if n == int(n) else f"{n:,.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


# ═══════════════════════════════════════════════════════════════════
# FORECAST ENGINE - FIXED
# ═══════════════════════════════════════════════════════════════════

class SalesForecastEngine:
    def __init__(self, sales_data: List[Dict], forecast_days: int):
        self.sales_data = sales_data
        self.forecast_days = forecast_days
        self.forecast_results = {
            'increasing': [],
            'decreasing': [],
            'stable': []
        }
        self.threshold = 5  # 5% threshold for significant change
    
    def validate_data(self) -> Tuple[bool, str]:
        """Validate if data is sufficient for forecasting"""
        unique_items = set(s.get('item_name') for s in self.sales_data if s.get('item_name'))
        total_sales = len(self.sales_data)
        
        # Less strict validation - just warn if not enough data
        if len(unique_items) < 2:
            return False, f"کم از کم 2 مختلف اشیاء کی ضرورت ہے۔ موجودہ: {len(unique_items)}"
        if total_sales < 3:
            return False, f"کم از کم 3 سیلز ریکارڈ کی ضرورت ہے۔ موجودہ: {total_sales}"
        return True, "OK"
    
    def prepare_item_data(self, item_sales: List[Dict]) -> pd.DataFrame:
        """Prepare DataFrame for forecasting"""
        df = pd.DataFrame([{
            'ds': s['sale_date'],
            'y': s['quantity_sold']
        } for s in item_sales])
        df['ds'] = pd.to_datetime(df['ds'])
        df = df.groupby('ds').agg({'y': 'sum'}).reset_index()
        df = df.sort_values('ds')
        return df
    
    def forecast_item(self, item_name: str, item_sales: List[Dict]) -> Dict:
        """Generate forecast for a single item"""
        try:
            df = self.prepare_item_data(item_sales)
            if len(df) < 2:
                return None
            
            # Calculate current average (last 7 days or all if less)
            recent_data = df.tail(min(7, len(df)))
            current_avg = recent_data['y'].mean() if len(recent_data) > 0 else df['y'].mean()
            
            if current_avg == 0:
                # Use quantity from sales
                current_avg = sum(s['quantity_sold'] for s in item_sales) / len(item_sales)
                if current_avg == 0:
                    return None
            
            # Calculate trend
            if len(df) >= 3:
                # Calculate linear trend
                x = np.arange(len(df))
                y = df['y'].values
                slope = np.polyfit(x, y, 1)[0]
                trend_per_day = slope
                forecast_avg = current_avg + (trend_per_day * self.forecast_days)
                forecast_avg = max(0, forecast_avg)
            else:
                # Simple average for less data
                forecast_avg = current_avg
            
            # Determine trend based on threshold
            change_pct = ((forecast_avg - current_avg) / current_avg) * 100 if current_avg > 0 else 0
            
            if change_pct > self.threshold:
                trend_type = 'increasing'
            elif change_pct < -self.threshold:
                trend_type = 'decreasing'
            else:
                trend_type = 'stable'
            
            return {
                'item_name': item_name,
                'trend': trend_type,
                'change_percentage': abs(change_pct),
                'current_avg': current_avg,
                'forecast_avg': forecast_avg,
                'total_sales': sum(s['quantity_sold'] for s in item_sales),
                'unit': item_sales[0].get('item_unit', 'عدد')
            }
            
        except Exception as e:
            print(f"Error forecasting {item_name}: {e}")
            return None
    
    def run_forecast(self) -> Dict:
        """Run forecast for all items"""
        item_sales_map = defaultdict(list)
        for sale in self.sales_data:
            item_sales_map[sale['item_name']].append(sale)
        
        for item_name, item_sales in item_sales_map.items():
            result = self.forecast_item(item_name, item_sales)
            if result:
                self.forecast_results[result['trend']].append(result)
        
        # Sort by change percentage
        self.forecast_results['increasing'].sort(key=lambda x: x['change_percentage'], reverse=True)
        self.forecast_results['decreasing'].sort(key=lambda x: x['change_percentage'], reverse=True)
        
        return self.forecast_results


# ═══════════════════════════════════════════════════════════════════
# CHART GENERATION (FIXED WITH UNICODE FONT)
# ═══════════════════════════════════════════════════════════════════

class ForecastChartGenerator:
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        plt.style.use('default')
        
        # Set matplotlib to use our Unicode font globally
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = [_unicode_mpl.get_name()]
    
    def create_summary_chart(self, forecasts: Dict) -> str:
        """Create summary pie chart with Urdu labels"""
        counts = {
            'بڑھنے والی': len(forecasts.get('increasing', [])),
            'گھٹنے والی': len(forecasts.get('decreasing', [])),
            'مستحکم': len(forecasts.get('stable', []))
        }
        counts = {k: v for k, v in counts.items() if v > 0}
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        if counts:
            colors_list = ['#2ecc71', '#e74c3c', '#95a5a6']
            wedges, texts, autotexts = ax.pie(
                counts.values(),
                labels=[_shape(label) for label in counts.keys()],
                autopct='%1.1f%%',
                colors=colors_list[:len(counts)],
                startangle=90,
                textprops={'fontproperties': _unicode_mpl, 'fontsize': 11}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_fontproperties(_unicode_mpl)
            for text in texts:
                text.set_fontproperties(_unicode_mpl)
        else:
            ax.text(0.5, 0.5, _shape('کافی ڈیٹا موجود نہیں ہے'), 
                   ha='center', va='center', fontsize=14,
                   fontproperties=_unicode_mpl)
        
        ax.set_title(_shape('فروخت کی پیشن گوئی کا خلاصہ'), 
                    fontproperties=_unicode_mpl, fontsize=14, fontweight='bold', pad=20)
        
        path = os.path.join(self.output_folder, 'summary_pie.png')
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        return path
    
    def create_trend_chart(self, forecasts: Dict, trend_type: str) -> str:
        """Create horizontal bar chart for trends"""
        items = forecasts.get(trend_type, [])[:8]
        if not items:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = [item['item_name'][:25] for item in items]
        changes = [item['change_percentage'] for item in items]
        
        # Shape names if they contain Urdu
        shaped_names = [_shape(name) if _is_rtl(name) else name for name in names]
        
        if trend_type == 'increasing':
            bars = ax.barh(range(len(names)), changes, color='#2ecc71')
            xlabel = _shape('متوقع اضافہ (%)')
            title = _shape('سب سے زیادہ فروخت بڑھنے والی اشیاء')
            sign = '+'
        else:
            bars = ax.barh(range(len(names)), changes, color='#e74c3c')
            xlabel = _shape('متوقع کمی (%)')
            title = _shape('سب سے زیادہ فروخت گھٹنے والی اشیاء')
            sign = '-'
        
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(shaped_names, fontproperties=_unicode_mpl, fontsize=10)
        ax.set_xlabel(xlabel, fontproperties=_unicode_mpl, fontsize=11)
        ax.set_title(title, fontproperties=_unicode_mpl, fontsize=14, fontweight='bold')
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax.grid(axis='x', alpha=0.3)
        
        for i, (bar, change) in enumerate(zip(bars, changes)):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{sign}{change:.1f}%', va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        path = os.path.join(self.output_folder, f'{trend_type}_items.png')
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        return path


# ═══════════════════════════════════════════════════════════════════
# PDF GENERATION (FIXED WITH UNICODE FONT)
# ═══════════════════════════════════════════════════════════════════

class ForecastPDFGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
    
    def _create_styles(self):
        return {
            'title': ParagraphStyle('Title', fontName=UNICODE_FONT, fontSize=20, 
                                    alignment=TA_CENTER, spaceAfter=20, spaceBefore=10),
            'heading': ParagraphStyle('Heading', fontName=UNICODE_FONT, fontSize=14, 
                                      textColor=colors.HexColor('#2C7DA0'), alignment=TA_CENTER, 
                                      spaceAfter=12, spaceBefore=15),
            'description': ParagraphStyle('Desc', fontName=UNICODE_FONT, fontSize=10,
                                          textColor=colors.HexColor('#5A6B7A'), alignment=TA_LEFT,
                                          spaceAfter=8, leading=16),
            'table_header': ParagraphStyle('TH', fontName=UNICODE_FONT, fontSize=11, 
                                           textColor=colors.white, alignment=TA_CENTER),
            'table_cell': ParagraphStyle('TC', fontName=UNICODE_FONT, fontSize=10, alignment=TA_CENTER)
        }
    
    def _p(self, text: str, style_name: str, styles: dict) -> Paragraph:
        """Create paragraph with proper shaping for Urdu"""
        txt = str(text).strip()
        display = _shape(txt) if _is_rtl(txt) else txt
        return Paragraph(display, styles[style_name])
    
    def generate_report(self, forecasts: Dict, charts: Dict, report_date: str, 
                       forecast_days: int, total_items: int) -> str:
        """Generate PDF report"""
        styles = self._create_styles()
        doc = SimpleDocTemplate(self.output_path, pagesize=A4,
                                rightMargin=55, leftMargin=55,
                                topMargin=55, bottomMargin=55)
        story = []
        
        # Title
        story.append(self._p(f"{forecast_days} دن کی فروخت کی پیشن گوئی رپورٹ", 'title', styles))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self._p(f"تاریخ: {report_date}", 'description', styles))
        story.append(Spacer(1, 0.2 * inch))
        
        # Summary
        story.append(self._p("رپورٹ کا خلاصہ", 'heading', styles))
        summary_text = f"""
        اس رپورٹ میں کل {total_items} اشیاء کا تجزیہ کیا گیا ہے۔ 
        ان میں سے {len(forecasts.get('increasing', []))} اشیاء کی فروخت میں اضافہ متوقع ہے، 
        {len(forecasts.get('decreasing', []))} اشیاء کی فروخت میں کمی متوقع ہے۔
        """
        story.append(self._p(summary_text, 'description', styles))
        story.append(Spacer(1, 0.2 * inch))
        
        # Summary Chart
        if charts.get('summary_pie') and os.path.exists(charts['summary_pie']):
            story.append(Image(charts['summary_pie'], width=5*inch, height=4*inch))
            story.append(Spacer(1, 0.1 * inch))
            pie_desc = "یہ چارٹ ظاہر کرتا ہے کہ کتنے فیصد اشیاء کی فروخت میں اضافہ، کمی متوقع ہے۔"
            story.append(self._p(pie_desc, 'description', styles))
            story.append(Spacer(1, 0.2 * inch))
        
        # Increasing Items (Top 5)
        if forecasts.get('increasing'):
            story.append(PageBreak())
            story.append(self._p("بڑھنے والی اشیاء (ٹاپ 5)", 'heading', styles))
            inc_desc = f"""
            درج ذیل {min(5, len(forecasts['increasing']))} اشیاء کی فروخت میں اگلے {forecast_days} دنوں میں 
            اضافہ متوقع ہے۔ ان اشیاء پر خصوصی توجہ دیں۔
            """
            story.append(self._p(inc_desc, 'description', styles))
            story.append(Spacer(1, 0.1 * inch))
            
            # Table
            table_data = [[
                self._p("درجہ", 'table_header', styles),
                self._p("آئٹم کا نام", 'table_header', styles),
                self._p("موجودہ اوسط", 'table_header', styles),
                self._p("متوقع اوسط", 'table_header', styles),
                self._p("متوقع اضافہ", 'table_header', styles)
            ]]
            
            for idx, item in enumerate(forecasts['increasing'][:5], 1):
                table_data.append([
                    self._p(str(idx), 'table_cell', styles),
                    self._p(item['item_name'], 'table_cell', styles),
                    self._p(f"{item['current_avg']:.1f} {item.get('unit', '')}", 'table_cell', styles),
                    self._p(f"{item['forecast_avg']:.1f} {item.get('unit', '')}", 'table_cell', styles),
                    self._p(f"+{item['change_percentage']:.1f}%", 'table_cell', styles)
                ])
            
            col_widths = [0.6*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))
            
            # Chart
            if charts.get('increasing_chart') and os.path.exists(charts['increasing_chart']):
                story.append(Image(charts['increasing_chart'], width=6*inch, height=4*inch))
        
        # Decreasing Items (Top 5)
        if forecasts.get('decreasing'):
            story.append(PageBreak())
            story.append(self._p("گھٹنے والی اشیاء (ٹاپ 5)", 'heading', styles))
            dec_desc = f"""
            درج ذیل {min(5, len(forecasts['decreasing']))} اشیاء کی فروخت میں اگلے {forecast_days} دنوں میں 
            کمی متوقع ہے۔ ان اشیاء پر پروموشنز دیں۔
            """
            story.append(self._p(dec_desc, 'description', styles))
            story.append(Spacer(1, 0.1 * inch))
            
            # Table
            table_data = [[
                self._p("درجہ", 'table_header', styles),
                self._p("آئٹم کا نام", 'table_header', styles),
                self._p("موجودہ اوسط", 'table_header', styles),
                self._p("متوقع اوسط", 'table_header', styles),
                self._p("متوقع کمی", 'table_header', styles)
            ]]
            
            for idx, item in enumerate(forecasts['decreasing'][:5], 1):
                table_data.append([
                    self._p(str(idx), 'table_cell', styles),
                    self._p(item['item_name'], 'table_cell', styles),
                    self._p(f"{item['current_avg']:.1f} {item.get('unit', '')}", 'table_cell', styles),
                    self._p(f"{item['forecast_avg']:.1f} {item.get('unit', '')}", 'table_cell', styles),
                    self._p(f"-{item['change_percentage']:.1f}%", 'table_cell', styles)
                ])
            
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))
            
            # Chart
            if charts.get('decreasing_chart') and os.path.exists(charts['decreasing_chart']):
                story.append(Image(charts['decreasing_chart'], width=6*inch, height=4*inch))
        
        doc.build(story)
        return self.output_path


# ═══════════════════════════════════════════════════════════════════
# EXCEL GENERATION - FIXED
# ═══════════════════════════════════════════════════════════════════

class ForecastExcelGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
    
    def generate_excel(self, forecasts: Dict, forecast_days: int) -> str:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        
        wb = Workbook()
        
        # Header style
        header_font = Font(bold=True, size=12, color="FFFFFF")
        header_fill = PatternFill(start_color="2C7DA0", end_color="2C7DA0", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center")
        
        # Cell style
        cell_align = Alignment(horizontal="center", vertical="center")
        
        # Sheet 1: Increasing Items
        if forecasts.get('increasing'):
            ws1 = wb.active
            ws1.title = "بڑھنے والی اشیاء"
            headers = ["درجہ", "آئٹم کا نام", "موجودہ اوسط", "متوقع اوسط", "متوقع اضافہ (%)", "یونٹ", "کل فروخت"]
            ws1.append(headers)
            
            # Style headers
            for col in range(1, len(headers)+1):
                cell = ws1.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align
            
            # Add data
            for idx, item in enumerate(forecasts['increasing'], 1):
                ws1.append([
                    idx, 
                    item['item_name'], 
                    f"{item['current_avg']:.1f}", 
                    f"{item['forecast_avg']:.1f}", 
                    f"+{item['change_percentage']:.1f}%",
                    item.get('unit', '-'),
                    fmt(item['total_sales'])
                ])
                # Style data cells
                for col in range(1, 8):
                    ws1.cell(row=idx+1, column=col).alignment = cell_align
            
            # Auto-adjust column widths
            for col in ws1.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                ws1.column_dimensions[col_letter].width = adjusted_width
        
        # Sheet 2: Decreasing Items
        if forecasts.get('decreasing'):
            ws2 = wb.create_sheet("گھٹنے والی اشیاء")
            headers = ["درجہ", "آئٹم کا نام", "موجودہ اوسط", "متوقع اوسط", "متوقع کمی (%)", "یونٹ", "کل فروخت"]
            ws2.append(headers)
            
            # Style headers
            for col in range(1, len(headers)+1):
                cell = ws2.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align
            
            # Add data
            for idx, item in enumerate(forecasts['decreasing'], 1):
                ws2.append([
                    idx, 
                    item['item_name'], 
                    f"{item['current_avg']:.1f}", 
                    f"{item['forecast_avg']:.1f}", 
                    f"-{item['change_percentage']:.1f}%",
                    item.get('unit', '-'),
                    fmt(item['total_sales'])
                ])
                for col in range(1, 8):
                    ws2.cell(row=idx+1, column=col).alignment = cell_align
            
            # Auto-adjust column widths
            for col in ws2.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                ws2.column_dimensions[col_letter].width = adjusted_width
        
        # Sheet 3: Summary
        ws3 = wb.create_sheet("خلاصہ")
        ws3.append(["تفصیل", "تعداد", "فیصد"])
        
        total = (len(forecasts.get('increasing', [])) + 
                len(forecasts.get('decreasing', [])) + 
                len(forecasts.get('stable', [])))
        
        if total > 0:
            inc_count = len(forecasts.get('increasing', []))
            dec_count = len(forecasts.get('decreasing', []))
            
            ws3.append(["بڑھنے والی اشیاء", inc_count, f"{inc_count/total*100:.1f}%"])
            ws3.append(["گھٹنے والی اشیاء", dec_count, f"{dec_count/total*100:.1f}%"])
            ws3.append(["مستحکم اشیاء", len(forecasts.get('stable', [])), f"{len(forecasts.get('stable', []))/total*100:.1f}%"])
        
        ws3.append([])
        ws3.append(["پیشن گوئی مدت", f"{forecast_days} دن"])
        
        # Style summary sheet
        for col in ws3.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws3.column_dimensions[col_letter].width = min(max_length + 2, 20)
        
        wb.save(self.output_path)
        return self.output_path


# ═══════════════════════════════════════════════════════════════════
# MAIN FORECAST REPORT FUNCTION
# ═══════════════════════════════════════════════════════════════════

async def generate_forecast_report(report_id: str, sales_data: List[Dict], forecast_days: int) -> Dict:
    """Main function to generate complete forecast report"""
    
    try:
        print(_urdu_msg(f"📊 پیشن گوئی رپورٹ تیار کر رہا ہے: {len(sales_data)} سیلز ریکارڈ, {forecast_days} دن"))
        
        # Create output folder
        output_folder = f"forecast_reports/report_{report_id}"
        os.makedirs(output_folder, exist_ok=True)
        
        # Run forecast
        forecaster = SalesForecastEngine(sales_data, forecast_days)
        
        # Validate data
        is_valid, message = forecaster.validate_data()
        if not is_valid:
            print(_urdu_msg(f"❌ {message}"))
            return {"error": True, "message": message}
        
        # Generate forecasts
        forecasts = forecaster.run_forecast()
        
        print(_urdu_msg(f"📈 پیشن گوئی کے نتائج: بڑھنے والی: {len(forecasts['increasing'])}, گھٹنے والی: {len(forecasts['decreasing'])}, مستحکم: {len(forecasts['stable'])}"))
        
        # Generate charts
        chart_gen = ForecastChartGenerator(output_folder)
        charts = {}
        
        # Summary pie chart
        charts['summary_pie'] = chart_gen.create_summary_chart(forecasts)
        print(_urdu_msg("✅ خلاصہ چارٹ تیار"))
        
        # Trend charts
        if forecasts.get('increasing'):
            charts['increasing_chart'] = chart_gen.create_trend_chart(forecasts, 'increasing')
            print(_urdu_msg("✅ بڑھنے والی اشیاء کا چارٹ تیار"))
        if forecasts.get('decreasing'):
            charts['decreasing_chart'] = chart_gen.create_trend_chart(forecasts, 'decreasing')
            print(_urdu_msg("✅ گھٹنے والی اشیاء کا چارٹ تیار"))
        
        # Generate PDF
        pdf_path = os.path.join(output_folder, f"forecast_report_{forecast_days}days.pdf")
        pdf_gen = ForecastPDFGenerator(pdf_path)
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        total_items = len(forecasts['increasing']) + len(forecasts['decreasing']) + len(forecasts['stable'])
        pdf_gen.generate_report(forecasts, charts, report_date, forecast_days, total_items)
        print(_urdu_msg(f"✅ PDF رپورٹ محفوظ: {pdf_path}"))
        
        # Generate Excel
        excel_path = os.path.join(output_folder, f"forecast_data_{forecast_days}days.xlsx")
        excel_gen = ForecastExcelGenerator(excel_path)
        excel_gen.generate_excel(forecasts, forecast_days)
        print(_urdu_msg(f"✅ ایکسل فائل محفوظ: {excel_path}"))
        
        # Generate CSV
        csv_path = os.path.join(output_folder, f"forecast_export_{forecast_days}days.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Item Name", "Trend", "Current Avg", "Forecast Avg", "Change %", "Unit", "Total Sales"])
            for item in forecasts.get('increasing', []):
                writer.writerow([item['item_name'], "Increasing", f"{item['current_avg']:.2f}", 
                               f"{item['forecast_avg']:.2f}", f"+{item['change_percentage']:.1f}%",
                               item.get('unit', ''), item['total_sales']])
            for item in forecasts.get('decreasing', []):
                writer.writerow([item['item_name'], "Decreasing", f"{item['current_avg']:.2f}", 
                               f"{item['forecast_avg']:.2f}", f"-{item['change_percentage']:.1f}%",
                               item.get('unit', ''), item['total_sales']])
        print(_urdu_msg(f"✅ CSV فائل محفوظ: {csv_path}"))
        
        print(_urdu_msg("🎉 تمام فائلیں کامیابی سے تیار ہو گئیں"))
        
        return {
            "error": False,
            "report_id": report_id,
            "output_folder": output_folder,
            "pdf_path": pdf_path,
            "excel_path": excel_path,
            "csv_path": csv_path,
            "forecast_summary": {
                "total_items_analyzed": total_items,
                "increasing_count": len(forecasts.get('increasing', [])),
                "decreasing_count": len(forecasts.get('decreasing', [])),
                "stable_count": len(forecasts.get('stable', [])),
                "forecast_days": forecast_days
            }
        }
        
    except Exception as e:
        print(_urdu_msg(f"❌ پیشن گوئی رپورٹ میں خرابی: {e}"))
        import traceback
        traceback.print_exc()
        return {"error": True, "message": str(e)}


async def delete_forecast_report(folder_path: str) -> Dict:
    """Delete forecast report folder"""
    import shutil
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        return {"status": "deleted", "path": folder_path}
    return {"status": "not_found", "path": folder_path}