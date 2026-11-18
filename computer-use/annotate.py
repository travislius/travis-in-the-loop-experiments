"""Annotate one run's screenshots: the frame the model saw + the action it chose (crosshair for clicks)."""
import json, sys, pathlib
from PIL import Image, ImageDraw, ImageFont
H = pathlib.Path(__file__).parent
run = H / sys.argv[1]; out = H / sys.argv[2]; out.mkdir(parents=True, exist_ok=True)
l = json.load(open(run / "log.json"))
F = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
prev = run / "shots/000.png"; frames = []
for s in l["steps"]:
    im = Image.open(prev).convert("RGB"); d = ImageDraw.Draw(im)
    if s["actions"]:
        a = s["actions"][0]; args = {k: v for k, v in a["args"].items() if k not in ("safety_decision", "intent")}
        if a.get("px"):
            x, y = a["px"]; d.ellipse([x - 26, y - 26, x + 26, y + 26], outline=(240, 70, 90), width=5)
            d.line([x - 40, y, x + 40, y], fill=(240, 70, 90), width=3); d.line([x, y - 40, x, y + 40], fill=(240, 70, 90), width=3)
        desc = a["name"] + "(" + ", ".join(f"{k}={v!r}" for k, v in args.items()) + ")"
        if a.get("safety_decision"): desc += "  → asks human to confirm"
    else:
        desc = "done: " + (s["text"] or "")[:70]
    d.rectangle([0, 730, 1280, 800], fill=(9, 11, 18)); d.text((24, 748), f"step {s['step']} · {s['latency_s']:.1f}s · {desc}"[:95], font=F, fill=(245, 245, 248))
    p = out / f"step{s['step']:02d}.png"; im.save(p); frames.append(p.name)
    if s["actions"] and s["actions"][-1].get("shot"): prev = run / s["actions"][-1]["shot"]
Image.open(prev).save(out / "final.png")
(out / "FRAMES.json").write_text(json.dumps({"run": str(run.relative_to(H)), "frames": frames}, indent=1)); print(len(frames))
