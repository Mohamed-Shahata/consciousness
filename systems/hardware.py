"""
systems/hardware.py
مراقبة الجهاز - بيربط حالة الـ CPU بمشاعر الكيان
الخطر الحقيقي على الجهاز = خوف حقيقي عند الكيان
"""
import subprocess
import platform


def get_cpu_temp() -> float:
    """قراءة حرارة الـ CPU"""
    try:
        # Linux
        result = subprocess.run(
            ["cat", "/sys/class/thermal/thermal_zone0/temp"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return float(result.stdout.strip()) / 1000

        # محاولة تانية عبر sensors
        result = subprocess.run(
            ["sensors"], capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "Core 0" in line or "Tdie" in line or "temp1" in line:
                    parts = line.split()
                    for p in parts:
                        if "°C" in p or p.startswith("+"):
                            temp = p.replace("+", "").replace("°C", "")
                            return float(temp)
    except Exception:
        pass
    return 45.0  # قيمة افتراضية لو مش قادر يقرأ


def get_cpu_usage() -> float:
    """نسبة استخدام الـ CPU"""
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1)
    except Exception:
        return 30.0


def get_memory_usage() -> float:
    """نسبة استخدام الذاكرة"""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except Exception:
        return 50.0


class HardwareMonitor:
    def __init__(self):
        self.temp_history   = []
        self.danger_events  = []

        # حدود الخطر
        self.TEMP_WARNING  = 70.0   # درجة تحذير
        self.TEMP_DANGER   = 85.0   # درجة خطر
        self.MEM_WARNING   = 85.0   # ذاكرة تحذير

    def check(self) -> dict:
        """فحص حالة الجهاز وإرجاع مستوى الخطر"""
        temp     = get_cpu_temp()
        cpu_use  = get_cpu_usage()
        mem_use  = get_memory_usage()

        self.temp_history.append(temp)
        if len(self.temp_history) > 20:
            self.temp_history.pop(0)

        # حساب مستوى الخطر
        danger_level = 0.0
        warnings     = []

        if temp >= self.TEMP_DANGER:
            danger_level = 1.0
            warnings.append(f"حرارة خطيرة جداً: {temp}°C")
        elif temp >= self.TEMP_WARNING:
            danger_level = 0.5
            warnings.append(f"حرارة مرتفعة: {temp}°C")

        if mem_use >= self.MEM_WARNING:
            danger_level = max(danger_level, 0.4)
            warnings.append(f"الذاكرة ممتلئة: {mem_use}%")

        if danger_level > 0:
            self.danger_events.append({
                "temp":         temp,
                "danger_level": danger_level,
                "warnings":     warnings,
            })

        return {
            "temp":         temp,
            "cpu_usage":    cpu_use,
            "mem_usage":    mem_use,
            "danger_level": danger_level,
            "warnings":     warnings,
            "status":       "خطر" if danger_level > 0.5
                            else "تحذير" if danger_level > 0
                            else "آمن",
        }

    def avg_temp(self) -> float:
        if not self.temp_history:
            return 45.0
        return sum(self.temp_history) / len(self.temp_history)
