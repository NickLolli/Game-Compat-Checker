"""
Week 2 TODO: CPU/GPU name -> benchmark score lookup table.

Start small and manual (a dict of ~30 common GPUs/CPUs covering the
last ~5 years), then consider importing a larger public dataset.
Keys should be normalized (lowercase, no punctuation) so lookups are
forgiving of formatting differences between Steam text and detected
hardware names.

Example shape:

GPU_SCORES = {
    "rtx 4090": 39000,
    "rtx 4070": 22000,
    "rtx 3060": 14500,
    "gtx 1660 super": 9500,
    "gtx 1050 ti": 4200,
    ...
}

CPU_SCORES = {
    "ryzen 7 7800x3d": 42000,
    "core i5-12400f": 24000,
    ...
}
"""

GPU_SCORES: dict[str, int] = {}
CPU_SCORES: dict[str, int] = {}
