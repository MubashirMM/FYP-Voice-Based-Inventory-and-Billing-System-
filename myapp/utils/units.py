class UnitConverter:
    def __init__(self):
        self.conversions = {
            # --- Weight units (modern simplified) ---
            "کلو": {
                "کلو": 1.0,
                "گرام": 1000.0,
                "پاؤ": 4.0,          # 1 کلو = 4 پاؤ
                "چھٹانک": 16.0,      # 1 کلو = 16 چھٹانک
                "سیر": 1.0,          # 1 سیر = 1 کلو
                "من": 1/40.0,        # 1 کلو = 1/40 من
                "بوری": 1/40.0,      # 1 کلو = 1/40 بوری
            },
            "گرام": {
                "گرام": 1.0,
                "کلو": 1/1000.0,
                "پاؤ": 1/250.0,
                "چھٹانک": 1/62.5,
                "سیر": 1/1000.0,
                "من": 1/40000.0,
                "بوری": 1/40000.0,
            },
            "پاؤ": {
                "پاؤ": 1.0,
                "کلو": 0.25,
                "گرام": 250.0,
                "چھٹانک": 4.0,
                "سیر": 0.25,
                "من": 0.25/40.0,
                "بوری": 0.25/40.0,
            },
            "چھٹانک": {
                "چھٹانک": 1.0,
                "پاؤ": 0.25,
                "کلو": 0.0625,
                "گرام": 62.5,
                "سیر": 0.0625,
                "من": 0.0625/40.0,
                "بوری": 0.0625/40.0,
            },
            "سیر": {
                "سیر": 1.0,
                "کلو": 1.0,
                "گرام": 1000.0,
                "پاؤ": 4.0,
                "چھٹانک": 16.0,
                "من": 1/40.0,
                "بوری": 1/40.0,
            },
            "من": {
                "من": 1.0,
                "کلو": 40.0,
                "گرام": 40000.0,
                "سیر": 40.0,
                "پاؤ": 160.0,
                "چھٹانک": 640.0,
                "بوری": 1.0,
            },
            "بوری": {
                "بوری": 1.0,
                "کلو": 40.0,
                "گرام": 40000.0,
                "سیر": 40.0,
                "پاؤ": 160.0,
                "چھٹانک": 640.0,
                "من": 1.0,
            },

            # --- Volume units ---
            "لیٹر": {
                "لیٹر": 1.0,
                "ملی لیٹر": 1000.0,
            },
            "ملی لیٹر": {
                "ملی لیٹر": 1.0,
                "لیٹر": 1/1000.0,
            },

            # --- Count units ---
            "عدد": {
                "عدد": 1.0,
                "درجن": 1/12.0,
                "آدھا درجن": 1/6.0,
            },
            "درجن": {
                "درجن": 1.0,
                "عدد": 12.0,
                "آدھا درجن": 0.5,
            },
            "آدھا درجن": {
                "آدھا درجن": 1.0,
                "عدد": 6.0,
                "درجن": 0.5,
            },

            # --- Packet units ---
            "پیکٹ": {"پیکٹ": 1.0, "ڈبہ": 1.0, "بوتل": 1.0},
            "ڈبہ": {"ڈبہ": 1.0, "پیکٹ": 1.0, "بوتل": 1.0},
            "بوتل": {"بوتل": 1.0, "پیکٹ": 1.0, "ڈبہ": 1.0},
        }

    def convert(self, base_unit: str, requested_unit: str, qty: float) -> float:
        base_unit = base_unit.strip()
        requested_unit = requested_unit.strip()
        if base_unit not in self.conversions:
            raise ValueError(f"بنیادی اکائی '{base_unit}' وضع نہیں کی گئی")
        if requested_unit not in self.conversions[base_unit]:
            raise ValueError(f"اکائی '{requested_unit}' کو '{base_unit}' میں تبدیل نہیں کیا جا سکتا")
        factor = self.conversions[base_unit][requested_unit]
        return qty * factor

    def is_compatible(self, base_unit: str, requested_unit: str) -> bool:
        base_unit = base_unit.strip()
        requested_unit = requested_unit.strip()
        return base_unit in self.conversions and requested_unit in self.conversions[base_unit]
