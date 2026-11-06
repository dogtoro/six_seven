"""Create a tiny fake dataset_sample/ so the pipeline can be tested before Zang delivers.
Usage: python make_mock_dataset.py --out ../dataset_sample_mock --n 12
"""
import argparse, json, os, random
import numpy as np
from PIL import Image, ImageDraw

p = argparse.ArgumentParser(); p.add_argument("--out", default="../dataset_sample_mock"); p.add_argument("--n", type=int, default=12)
a = p.parse_args()
for d in ("images", "masks"): os.makedirs(os.path.join(a.out, d), exist_ok=True)
recs = []
for i in range(a.n):
    random.seed(i)
    img = Image.new("RGB", (400, 600), (20, 24, 40)); d = ImageDraw.Draw(img)
    for k in range(8): d.text((30, 40 + k * 60), f"Field {k}: {random.randint(10**5, 10**6)}", fill=(230, 230, 230))
    tpl = ["vcb", "mb", "tech"][i % 3]
    for qf in (95, 85, 75):
        # authentic
        aid = f"{tpl}_{i:03d}_auth_q{qf}"
        img.save(f"{a.out}/images/{aid}.jpg", quality=qf)
        recs.append(dict(id=aid, image=f"images/{aid}.jpg", mask=None, label=0, template=tpl, tamper_type="none", compression=f"jpeg{qf}", pair=f"{tpl}_{i:03d}"))
        # tampered
        t = img.copy(); dd = ImageDraw.Draw(t); y = 40 + 3 * 60
        dd.rectangle([30, y, 250, y + 14], fill=(20, 24, 40)); dd.text((30, y), "Field 3: 999999", fill=(230, 230, 230))
        m = np.zeros((600, 400), np.uint8); m[y:y + 14, 30:250] = 255
        tid = f"{tpl}_{i:03d}_amount_q{qf}"
        t.save(f"{a.out}/images/{tid}.jpg", quality=qf); Image.fromarray(m).save(f"{a.out}/masks/{tid}.png")
        recs.append(dict(id=tid, image=f"images/{tid}.jpg", mask=f"masks/{tid}.png", label=1, template=tpl, tamper_type="amount", compression=f"jpeg{qf}", pair=f"{tpl}_{i:03d}", bbox=[30, y, 250, y + 14]))
json.dump(recs, open(f"{a.out}/metadata.json", "w"), indent=1)
print("wrote", len(recs), "records to", a.out)
