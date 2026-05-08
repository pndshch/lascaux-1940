#!/usr/bin/env python3
"""Generate gameplay GIF for lascaux-1940 using headless Chrome ?frame= harness."""
import subprocess
from pathlib import Path
from PIL import Image

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = "http://127.0.0.1:8771"
OUT_DIR = Path("/tmp/lascaux-1940/frames")
OUT_GIF = Path("/tmp/lascaux-1940.gif")

# Render in 400-wide window; page is constrained to 540 max-width on desktop
# but we want a phone-aspect crop. The hub displays 320x611. Use that.
WIN_W, WIN_H = 360, 651
GIF_W, GIF_H = 320, 611

# (frame_index, virtual_time_budget_ms, gif_duration_ms, label)
FRAMES = [
    (0, 1200, 1400, "intro"),
    (1, 1500, 900,  "torch-sweep"),
    (2, 4500, 1300, "auroch-reveal"),
    (3, 4500, 1100, "horse-reveal"),
    (4, 4500, 1100, "shaft-reveal"),
    (5, 1500, 2000, "end-clipping"),
]

OUT_DIR.mkdir(parents=True, exist_ok=True)
for f in OUT_DIR.glob("*.png"):
    f.unlink()

screenshots = []
durations = []
for i, (frame, vtb, dur, label) in enumerate(FRAMES):
    out = OUT_DIR / f"{i:02d}_{label}.png"
    cmd = [
        CHROME,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        f"--window-size={WIN_W},{WIN_H}",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        f"--virtual-time-budget={vtb}",
        f"--screenshot={out}",
        f"{URL}/?frame={frame}&t={i}&v={vtb}",
    ]
    print(f"[{i}] {label}: state={frame} vtb={vtb}ms ...", flush=True)
    subprocess.run(cmd, capture_output=True, timeout=60)
    if out.exists():
        screenshots.append(out)
        durations.append(dur)
        print(f"     -> {out.stat().st_size} bytes")
    else:
        print(f"     !! missing")

imgs = []
for s in screenshots:
    im = Image.open(s).convert("RGB")
    im = im.resize((WIN_W, WIN_H), Image.LANCZOS)
    # Game is anchored at top-left in gifmode; crop top-left 320x611
    target = im.crop((0, 0, GIF_W, GIF_H))
    imgs.append(target)

if imgs:
    palette_im = imgs[0].quantize(colors=80, method=Image.FASTOCTREE)
    quantized = [im.quantize(colors=80, method=Image.FASTOCTREE, palette=palette_im) for im in imgs]
    quantized[0].save(
        OUT_GIF,
        save_all=True,
        append_images=quantized[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"\nGIF: {OUT_GIF}  ({OUT_GIF.stat().st_size:,} bytes, {len(quantized)} frames)")
else:
    print("No frames captured")
