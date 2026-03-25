from typing import Dict, Tuple

FRACTIONAL_PREFIXES = {
    "آدھا": 0.5,
    "ڈیڑھ": 1.5,
    "ڈھائی": 2.5,
}

class UnitConverter:
    def __init__(self):
        self.conversions: Dict[str, Dict[str, float]] = {
            # Weight
            "کلو": {"کلو": 1.0, "گرام": 1000.0, "پاؤ": 4.0, "چھٹانک": 16.0, "سیر": 1.0, "من": 1/40.0, "بوری": 1/50.0},
            "گرام": {"گرام": 1.0, "کلو": 1/1000.0, "پاؤ": 1/250.0, "چھٹانک": 1/62.5, "سیر": 1/1000.0, "من": 1/40000.0, "بوری": 1/50000.0},
            "پاؤ": {"پاؤ": 1.0, "کلو": 0.25, "گرام": 250.0, "چھٹانک": 4.0, "سیر": 0.25, "من": 0.25/40.0, "بوری": 0.25/50.0},
            "چھٹانک": {"چھٹانک": 1.0, "پاؤ": 0.25, "کلو": 0.0625, "گرام": 62.5, "سیر": 0.0625, "من": 0.0625/40.0, "بوری": 0.0625/50.0},
            "سیر": {"سیر": 1.0, "کلو": 1.0, "گرام": 1000.0, "پاؤ": 4.0, "چھٹانک": 16.0, "من": 1/40.0, "بوری": 1/50.0},
            "من": {"من": 1.0, "کلو": 40.0, "گرام": 40000.0, "سیر": 40.0, "پاؤ": 160.0, "چھٹانک": 640.0, "بوری": 40.0/50.0},
            "بوری": {"بوری": 1.0, "کلو": 50.0, "گرام": 50000.0, "سیر": 50.0, "پاؤ": 200.0, "چھٹانک": 800.0, "من": 50.0/40.0},

            # Volume
            "لیٹر": {"لیٹر": 1.0, "ملی لیٹر": 1000.0},
            "ملی لیٹر": {"ملی لیٹر": 1.0, "لیٹر": 1/1000.0},

            # Count
            "عدد": {"عدد": 1.0, "درجن": 1/12.0, "آدھا درجن": 1/6.0},
            "درجن": {"درجن": 1.0, "عدد": 12.0, "آدھا درجن": 0.5},
            "آدھا درجن": {"آدھا درجن": 1.0, "عدد": 6.0, "درجن": 0.5},

            # Package (same unit family)
            "پیکٹ": {"پیکٹ": 1.0, "ڈبہ": 1.0, "بوتل": 1.0},
            "ڈبہ": {"ڈبہ": 1.0, "پیکٹ": 1.0, "بوتل": 1.0},
            "بوتل": {"بوتل": 1.0, "پیکٹ": 1.0, "ڈبہ": 1.0},
        }

    def normalize_unit(self, unit: str, quantity: float = 1.0) -> Tuple[str, float]:
        """Handle fractional prefixes like آدھا, ڈیڑھ, ڈھائی"""
        unit = unit.strip()
        for prefix, factor in FRACTIONAL_PREFIXES.items():
            if unit.startswith(prefix):
                base_unit = unit[len(prefix):].strip()
                return base_unit, quantity * factor
        return unit, quantity

    def convert(self, from_unit: str, to_unit: str, value: float) -> float:
        """Convert quantity from one unit to another"""
        from_unit, value = self.normalize_unit(from_unit, value)
        to_unit = to_unit.strip()

        if from_unit not in self.conversions:
            raise ValueError(f"بنیادی اکائی نہیں ملی: {from_unit}")

        if to_unit not in self.conversions[from_unit]:
            raise ValueError(f"اس اکائی میں تبدیل نہیں ہو سکتا: {from_unit} → {to_unit}")

        factor = self.conversions[from_unit][to_unit]
        return value * factor

    def is_compatible(self, unit1: str, unit2: str) -> bool:
        """Check if two units belong to same category"""
        unit1, _ = self.normalize_unit(unit1)
        unit2, _ = self.normalize_unit(unit2)

        if unit1 not in self.conversions:
            return False
        return unit2 in self.conversions[unit1]