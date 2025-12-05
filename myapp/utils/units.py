# utils/unit_conversion.py
class UnitConverter:
    def __init__(self):
        self.conversions = {
            "کلو": {
                "کلو": 1.0,
                "گرام": 1/1000.0,
                "پاؤ": 0.25,       # 1 پاؤ = 0.25 کلو
                "چھٹانک": 0.0625,  # 1 چھٹانک = 1/16 کلو
                "آدھا کلو": 0.5,
                "ڈیڑھ کلو": 1.5,
                "ڈھائی کلو": 2.5,
                "بوری": 40.0,     # 1 بوری = 40 کلو (typical)
            },
            "لیٹر": {
                "لیٹر": 1.0,
                "ملی لیٹر": 1/1000.0,
                "آدھا لیٹر": 0.5,
                "ڈیڑھ لیٹر": 1.5,
            },
            "پیکٹ": {
                "پیکٹ": 1.0,
                "ڈبہ": 1.0,
                "بوتل": 1.0,
            },
            "عدد": {
                "عدد": 1.0,
                "درجن": 12.0,
                "آدھا درجن": 6.0,
            },
        }

    def convert(self, base_unit: str, requested_unit: str, qty: float) -> float:
        """Convert requested unit to base unit, returns quantity in base unit"""
        base_unit = base_unit.strip()
        requested_unit = requested_unit.strip()

        if base_unit not in self.conversions:
            raise ValueError(f"بنیادی اکائی '{base_unit}' وضع نہیں کی گئی")

        if requested_unit not in self.conversions[base_unit]:
            raise ValueError(f"اکائی '{requested_unit}' کو '{base_unit}' میں تبدیل نہیں کیا جا سکتا")

        factor = self.conversions[base_unit][requested_unit]
        return qty * factor

    def is_compatible(self, base_unit: str, requested_unit: str) -> bool:
        """Check if units are compatible"""
        try:
            base_unit = base_unit.strip()
            requested_unit = requested_unit.strip()
            return base_unit in self.conversions and requested_unit in self.conversions[base_unit]
        except:
            return False