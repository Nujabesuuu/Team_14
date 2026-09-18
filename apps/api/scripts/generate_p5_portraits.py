"""Generate hero portraits in a flat, high-contrast cel-shaded style on solid red.

Style target: bold black ink outlines, two-tone flat shading, no gradients or painterly blur,
solid red background, dynamic three-quarter pose, stylised phantom-thief outfit. Original characters.

Usage: python scripts/generate_p5_portraits.py <out_dir> [key ...] [--seeds 2]
"""

import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

STYLE = (
    "flat cel-shaded anime illustration, thick bold black ink outlines, two-tone flat shading, "
    "no gradients, no soft shading, high contrast, solid bright red background, dynamic three-quarter "
    "bust pose, stylish black long coat with silver zipper details, confident smirk, sharp angular hair, "
    "vector-like clean shapes, character select splash art, no text, no watermark, no logo"
)

SUBJECTS = {
    "duelist": "young woman duelist with a short dark red bob, one hand raised pointing forward, red gloves",
    "sage": "calm young man with dark blue hair covering one eye, hand touching his temple, teal gloves",
    "impostor": "grinning young man with spiky blond hair pointing at the viewer, yellow gloves, red scarf",
    "builder": "sturdy young woman with a bandana and rolled sleeves, arms crossed, green gloves",
    "pilot": "young man with goggles pushed up in his hair, thumb hooked in collar, blue gloves",
    "operator": "focused young woman with a tight ponytail and a headset, side glance, grey gloves",
    "vanguard": "broad-shouldered young man with a spiked collar, chin up, orange gloves",
    "strategist": "young woman with glasses and a sharp brown bob, hand adjusting glasses, purple gloves",
    "guide": "friendly android with a soft smile and subtle circuit lines on the cheek, gold gloves",
}


def fetch(prompt: str, out: Path, seed: int, size: int = 640) -> bool:
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt)
        + f"?width={size}&height={size + 64}&nologo=true&seed={seed}&model=flux"
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                data = r.read()
            if len(data) < 5000:
                raise OSError("tiny response")
            out.write_bytes(data)
            subprocess.run(
                ["sips", "-c", str(size), str(size), "--cropOffset", "0", "0", str(out)],
                check=False,
                capture_output=True,
            )
            print(f"ok   {out.name} ({len(data) // 1024} KB)", flush=True)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"retry {out.name}: {exc}", flush=True)
            time.sleep(3 * (attempt + 1))
    print(f"FAIL {out.name}", flush=True)
    return False


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    seeds = 2
    if "--seeds" in sys.argv:
        seeds = int(sys.argv[sys.argv.index("--seeds") + 1])
    out_dir = Path(args[0])
    keys = args[1:] or list(SUBJECTS)
    out_dir.mkdir(parents=True, exist_ok=True)
    for key in keys:
        for s in range(seeds):
            fetch(f"{SUBJECTS[key]}, {STYLE}", out_dir / f"{key}-{s + 1}.jpg", seed=500 + s * 17 + len(key))


if __name__ == "__main__":
    main()
