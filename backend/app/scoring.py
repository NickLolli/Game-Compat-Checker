"""
Week 2: Comparison / verdict logic.

Takes a user's hardware (from hardware.py's detect_hardware(), or
manually typed in for "custom PC builder" mode) and a game's parsed
requirements (from steam.py - not built yet, so for now we accept a
plain dict in the same shape - see the __main__ demo below), and
produces a verdict: how well will this run, and what should you
upgrade if it won't.

EXPECTED SHAPES
----------------
user_specs = {
    "cpu": {"name": "Intel(R) Core(TM) Ultra 7 155H", ...},
    "ram": {"total_gb": 15.4},
    "gpus": [{"name": "Intel(R) Arc(TM) Graphics", "vram_gb": 2.0}],
}

game_requirements = {
    "minimum":     {"cpu": "Core i5-8400", "gpu": "GTX 1050 Ti", "ram_gb": 8},
    "recommended": {"cpu": "Core i7-9700K", "gpu": "RTX 2060",   "ram_gb": 16},
}
(This shape is a placeholder until steam.py's parser is built in Week 3
and produces real data in this format.)
"""

from app.benchmarks import GPU_SCORES, CPU_SCORES, find_score

# How far above "recommended" counts as "Very good" rather than just "Good"
VERY_GOOD_MULTIPLIER = 1.1


def _best_gpu(gpus: list[dict]) -> dict:
    """If a machine has multiple GPUs (integrated + dedicated), pick
    whichever scores higher for the comparison - that's the one a game
    will actually use."""
    if len(gpus) == 1:
        return gpus[0]

    scored = [(find_score(g["name"], GPU_SCORES)[0] or 0, g) for g in gpus]
    return max(scored, key=lambda pair: pair[0])[1]


def _component_ratio(user_score: int | None, required_score: int | None) -> float | None:
    """user_score / required_score. None if either side couldn't be
    scored (unknown hardware) - caller should treat None as 'unable to
    compare this component' rather than a failure."""
    if user_score is None or required_score is None or required_score == 0:
        return None
    return round(user_score / required_score, 2)


def compare_specs(user_specs: dict, game_requirements: dict) -> dict:
    gpu = _best_gpu(user_specs["gpus"])
    user_gpu_score, gpu_match = find_score(gpu["name"], GPU_SCORES)
    user_cpu_score, cpu_match = find_score(user_specs["cpu"]["name"], CPU_SCORES)
    user_ram_gb = user_specs["ram"]["total_gb"]

    minimum = game_requirements["minimum"]
    recommended = game_requirements["recommended"]

    min_gpu_score, _ = find_score(minimum["gpu"], GPU_SCORES)
    min_cpu_score, _ = find_score(minimum["cpu"], CPU_SCORES)
    rec_gpu_score, _ = find_score(recommended["gpu"], GPU_SCORES)
    rec_cpu_score, _ = find_score(recommended["cpu"], CPU_SCORES)

    ratios_vs_recommended = {
        "gpu": _component_ratio(user_gpu_score, rec_gpu_score),
        "cpu": _component_ratio(user_cpu_score, rec_cpu_score),
        "ram": _component_ratio(user_ram_gb, recommended["ram_gb"]),
    }
    ratios_vs_minimum = {
        "gpu": _component_ratio(user_gpu_score, min_gpu_score),
        "cpu": _component_ratio(user_cpu_score, min_cpu_score),
        "ram": _component_ratio(user_ram_gb, minimum["ram_gb"]),
    }

    verdict = _determine_verdict(ratios_vs_recommended, ratios_vs_minimum)
    bottleneck = _find_bottleneck(ratios_vs_minimum)

    return {
        "verdict": verdict,
        "bottleneck": bottleneck,
        "matched_hardware": {"gpu": gpu_match, "cpu": cpu_match},
        "ratios_vs_recommended": ratios_vs_recommended,
        "ratios_vs_minimum": ratios_vs_minimum,
        "unmatched_components": [
            comp for comp, ratio in ratios_vs_minimum.items() if ratio is None
        ],
        # Reference-only info, not scored - we don't detect the
        # user's free disk space or exact OS build number, so there's
        # nothing to meaningfully compare these against. Passed
        # through so the frontend can just display them for context.
        "reference_info": {
            "minimum": {
                "os": minimum.get("os"),
                "directx": minimum.get("directx"),
                "storage": minimum.get("storage"),
            },
            "recommended": {
                "os": recommended.get("os"),
                "directx": recommended.get("directx"),
                "storage": recommended.get("storage"),
            },
        },
    }


def _determine_verdict(vs_recommended: dict, vs_minimum: dict) -> str:
    # Ignore RAM in the "how good" verdict tiers below minimum, since
    # RAM is usually a hard pass/fail rather than a performance slider
    # the way GPU/CPU speed is - but still factor it into "unplayable".
    core_ratios_rec = [v for k, v in vs_recommended.items() if k != "ram" and v is not None]
    core_ratios_min = [v for k, v in vs_minimum.items() if k != "ram" and v is not None]

    if not core_ratios_min:
        return "Unknown (couldn't match your hardware to known benchmarks)"

    if vs_minimum.get("ram") is not None and vs_minimum["ram"] < 1.0:
        return "Unplayable (insufficient RAM)"

    if min(core_ratios_min) < 1.0:
        return "Unplayable"

    if core_ratios_rec and min(core_ratios_rec) >= VERY_GOOD_MULTIPLIER:
        return "Very good"

    if core_ratios_rec and min(core_ratios_rec) >= 1.0:
        return "Good"

    return "Playable (lower settings recommended)"


def _find_bottleneck(vs_minimum: dict) -> str | None:
    """Whichever component has the lowest ratio vs. minimum requirement
    is the one holding you back most - that's what to upgrade first."""
    valid = {k: v for k, v in vs_minimum.items() if v is not None}
    if not valid:
        return None
    worst_component = min(valid, key=valid.get)
    if valid[worst_component] >= VERY_GOOD_MULTIPLIER:
        return None  # nothing is really a bottleneck
    return worst_component


if __name__ == "__main__":
    import json
    from app.hardware import detect_hardware

    # Placeholder game requirements until steam.py parses real ones -
    # this example is roughly Cyberpunk 2077's published requirements.
    demo_requirements = {
        "minimum": {"cpu": "Core i5-8400", "gpu": "GTX 1060", "ram_gb": 8},
        "recommended": {"cpu": "Core i7-9700K", "gpu": "RTX 2060", "ram_gb": 16},
    }

    user_specs = detect_hardware()
    result = compare_specs(user_specs, demo_requirements)
    print(json.dumps(result, indent=2))