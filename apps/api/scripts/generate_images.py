"""Generate avatar archetypes and seed profile photos with Pollinations (free, keyless).

Usage: python scripts/generate_images.py [--force]
Outputs:
    apps/web/public/avatars/<key>.jpg      8 hero archetypes + guide bot
    apps/api/app/seed_assets/<email>.jpg   12 seed profile "photos"
"""

import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AVATAR_DIR = ROOT / "apps" / "web" / "public" / "avatars"
PHOTO_DIR = ROOT / "apps" / "api" / "app" / "seed_assets"

STYLE = (
    "flat anime portrait illustration, bold black ink outlines, limited palette, one accent color, "
    "stylized jrpg character select art, confident expression, centered bust shot, plain dark background, "
    "clean vector-like shading, no text, no watermark"
)

# key -> (accent, subject). Original archetypes, not existing game characters.
ARCHETYPES = {
    "duelist": ("crimson red", "young agile duelist with a short blade and a wind-swept hood"),
    "sage": ("jade green", "calm healer with a glowing orb and a serene half-mask"),
    "impostor": ("bright teal", "mischievous character in a rounded space suit with a dark visor and a sly grin"),
    "builder": ("moss green", "blocky adventurer with a pickaxe over the shoulder and a square-jawed grin"),
    "pilot": ("electric blue", "rocket car pilot with a sleek helmet, goggles pushed up, cocky smile"),
    "operator": ("steel grey", "focused sniper operator with a tactical cap and a headset"),
    "vanguard": ("burnt orange", "broad-shouldered tank warrior with heavy pauldrons and a tower shield edge"),
    "strategist": ("royal purple", "sharp-eyed strategist with glasses, headset and a holographic map glow"),
    "guide": ("warm gold", "friendly android guide with a soft smile, subtle circuit lines, gentle glow"),
}

PHOTO_STYLE = (
    "candid portrait photo of a young adult gamer, natural window light, soft bokeh, "
    "wearing a hoodie or tee, relaxed genuine expression, headphones around neck, "
    "35mm film look, shallow depth of field, no text, no watermark"
)

SEED_PHOTOS = {
    "user01": "woman in her early twenties with a fox-red bob and freckles, small smile",
    "user02": "man in his mid twenties with dark tousled hair and a confident grin, blue hoodie",
    "user03": "woman with long wavy brown hair and round glasses, cozy oversized sweater",
    "user04": "tall man with a beard and a beanie, tired but kind eyes",
    "user05": "woman with a sharp black bob and a leather jacket, direct gaze",
    "user06": "young man with bleached curly hair and a playful smirk, orange tee",
    "user07": "woman with soft pink hair and a pastel cardigan, warm laugh",
    "user08": "athletic man with a buzz cut and a cyan windbreaker, morning light",
    "user09": "woman with braids and a green bomber jacket, thoughtful look",
    "user10": "man with a man-bun and a grey hoodie, arms crossed, slight smile",
    "user11": "woman with auburn hair in a loose ponytail, sunflower-yellow top",
    "user12": "man with glasses and a navy flannel, gentle expression",
    "guide": "friendly android guide with a soft smile, subtle circuit lines, gentle golden glow, studio portrait",
}


def fetch(prompt: str, out: Path, seed: int, size: int, force: bool) -> None:
    if out.exists() and not force:
        print(f"skip {out.name}")
        return
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
            # Crop the bottom strip (provider watermark) and resize with macOS sips.
            subprocess.run(
                ["sips", "-c", str(size), str(size), "--cropOffset", "0", "0", str(out)],
                check=False,
                capture_output=True,
            )
            print(f"ok   {out.name} ({len(data) // 1024} KB)")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"retry {out.name}: {exc}")
            time.sleep(3 * (attempt + 1))
    print(f"FAIL {out.name}")


def main() -> None:
    force = "--force" in sys.argv
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    for i, (key, (accent, subject)) in enumerate(ARCHETYPES.items()):
        fetch(f"{subject}, {accent} accent, {STYLE}", AVATAR_DIR / f"{key}.jpg", seed=100 + i, size=512, force=force)
    for i, (key, subject) in enumerate(SEED_PHOTOS.items()):
        fetch(f"{subject}, {PHOTO_STYLE}", PHOTO_DIR / f"{key}.jpg", seed=200 + i, size=640, force=force)


if __name__ == "__main__":
    main()
