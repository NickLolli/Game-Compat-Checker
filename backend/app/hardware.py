"""
Week 1: Local hardware detection.

Reads the current machine's CPU, RAM, and GPU and returns it as a
plain dict so the rest of the app (scoring.py) can compare it against
a game's requirements without caring how the data was collected.

NOTE: NVIDIA GPU detection via GPUtil/pynvml only works if the NVIDIA
driver + nvidia-smi are installed. AMD/Intel GPU detection needs a
different path (see the TODO below) - fine to punt on for now and
just support NVIDIA + a manual override.
"""

import platform
import psutil

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False


def get_cpu_info() -> dict:
    return {
        "name": platform.processor() or "Unknown CPU",
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": getattr(psutil.cpu_freq(), "max", None),
    }


def get_ram_info() -> dict:
    total_bytes = psutil.virtual_memory().total
    return {
        "total_gb": round(total_bytes / (1024 ** 3), 1),
    }


def get_gpu_info() -> list[dict]:
    """Returns a list since a machine can have multiple GPUs."""
    if not HAS_GPUTIL:
        return [{"name": "Unknown (GPUtil not available)", "vram_gb": None}]

    gpus = GPUtil.getGPUs()
    if not gpus:
        return [{"name": "No NVIDIA GPU detected", "vram_gb": None}]

    return [
        {
            "name": gpu.name,
            "vram_gb": round(gpu.memoryTotal / 1024, 1),
            "driver": gpu.driver,
        }
        for gpu in gpus
    ]


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
