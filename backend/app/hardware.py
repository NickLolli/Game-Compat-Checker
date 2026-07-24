"""
Week 1: Local hardware detection.

Reads the current machine's CPU, RAM, and GPU and returns it as a
plain dict so the rest of the app (scoring.py) can compare it against
a game's requirements without caring how the data was collected.

NOTE on GPU detection: GPUtil only works for NVIDIA cards (via
nvidia-smi) and is unmaintained/broken on Python 3.12+ (depends on
the removed `distutils` module). Instead, on Windows we query WMI
directly via the `wmi` package, which works for any GPU vendor
(NVIDIA, AMD, Intel) since it just reads what Windows already knows.
It only gives static info (model name, VRAM) rather than live
utilization - that's fine for our comparison use case.
"""

import platform
import psutil

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import wmi
        HAS_WMI = True
    except ImportError:
        HAS_WMI = False
else:
    HAS_WMI = False


def get_cpu_info() -> dict:
    # platform.processor() returns a raw CPUID string (e.g. "Intel64
    # Family 6 Model 170..."), not the marketing name Steam's
    # requirements text uses (e.g. "Core Ultra 7 155H"). WMI has the
    # real name Windows shows in Task Manager, plus a more reliable
    # max clock speed than psutil.cpu_freq() (which on Windows often
    # reports the current/throttled speed instead of true max).
    name = platform.processor() or "Unknown CPU"
    max_freq_mhz = getattr(psutil.cpu_freq(), "max", None)

    if IS_WINDOWS and HAS_WMI:
        w = wmi.WMI()
        processors = w.Win32_Processor()
        if processors:
            cpu = processors[0]  # multi-socket systems are rare enough to ignore for now
            name = cpu.Name.strip()
            if cpu.MaxClockSpeed:
                max_freq_mhz = cpu.MaxClockSpeed

    return {
        "name": name,
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": max_freq_mhz,
    }


def get_ram_info() -> dict:
    total_bytes = psutil.virtual_memory().total
    return {
        "total_gb": round(total_bytes / (1024 ** 3), 1),
    }


def get_gpu_info() -> list[dict]:
    """Returns a list since a machine can have multiple GPUs
    (e.g. a laptop with integrated + dedicated graphics)."""
    if not IS_WINDOWS:
        return [{"name": "GPU detection only implemented for Windows so far", "vram_gb": None}]

    if not HAS_WMI:
        return [{"name": "Unknown (run: pip install wmi)", "vram_gb": None}]

    w = wmi.WMI()
    controllers = w.Win32_VideoController()

    if not controllers:
        return [{"name": "No GPU detected via WMI", "vram_gb": None}]

    results = []
    for gpu in controllers:
        # AdapterRAM is a 32-bit field in WMI and overflows/reports
        # incorrectly for cards with >4GB VRAM on some Windows
        # versions - flag as None rather than show a wrong number.
        vram_gb = None
        if gpu.AdapterRAM and gpu.AdapterRAM > 0:
            raw_gb = gpu.AdapterRAM / (1024 ** 3)
            vram_gb = round(raw_gb, 1) if raw_gb < 4 else None

        results.append({
            "name": gpu.Name,
            "vram_gb": vram_gb,
            "driver_version": gpu.DriverVersion,
        })

    return results


def detect_hardware() -> dict:
    """Single entrypoint the API layer will call."""
    return {
        "os": platform.system(),
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "gpus": get_gpu_info(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(detect_hardware(), indent=2))