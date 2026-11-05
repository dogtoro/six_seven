"""Convert TextShield-R1 (MLLM) text answers into the prob maps eval_sota.py expects.
TextShield-R1 (github.com/qcf-568/TextShield, Qwen2.5-VL via ms-swift) does NOT output a heatmap: it outputs text + bounding boxes.
We rasterize predicted boxes into a binary map (1.0 inside box), and the image-level score = 1.0 if it answers "tampered" else 0.0.
=> its AUC is degenerate (binary score); report detection accuracy/F1 instead, and say so in the report.

Inference (from the repo README):
  python convert_image_dir_to_json.py --input <dir of invoice images>          # in the TextShield repo
  CUDA_VISIBLE_DEVICES=0 swift infer --model <textshield model dir> --val_dataset <json> --max_new_tokens 4096 --model_type qwen2_5_vl
Then:  python textshield_to_maps.py --result <swift result .jsonl> --data ../dataset_sample --out preds/textshield
!! VERIFY on 1-2 samples: (a) the jsonl key holding the answer (assumed "response"), (b) the box format/coordinate space.
   Assumed: 4-number groups [x1,y1,x2,y2] in pixels of the image the model saw; use --norm1000 if coordinates are 0-1000 normalized.
"""
import argparse, json, os, re
import numpy as np
from PIL import Image

NUM = r"-?\d+(?:\.\d+)?"
BOX = re.compile(rf"\(?\[?\s*({NUM})\s*,\s*({NUM})\s*,\s*({NUM})\s*,\s*({NUM})\s*\]?\)?|\(({NUM}),\s*({NUM})\)\s*,\s*\(({NUM}),\s*({NUM})\)")


def parse(resp):
    ans = re.search(r"<answer>(.*?)</answer>", resp, re.S); ans = ans.group(1) if ans else resp
    low = ans.lower()
    tampered = ("tampered" in low or "forged" in low) and not re.search(r"(not|n't|no)\s+(been\s+)?tampered|authentic|genuine|real image", low)
    boxes = []
    for m in BOX.finditer(ans):
        g = [x for x in m.groups() if x is not None]
        if len(g) == 4: boxes.append([float(v) for v in g])
    return tampered, boxes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True); ap.add_argument("--data", default="../dataset_sample"); ap.add_argument("--out", default="preds/textshield")
    ap.add_argument("--norm1000", action="store_true"); ap.add_argument("--resp-key", default="response")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    n = 0
    for line in open(a.result):
        if not line.strip(): continue
        d = json.loads(line)
        resp = d.get(a.resp_key) or d.get("response") or ""
        img = d.get("images", [None])[0] or d.get("image") or (d.get("images") or [{}])[0]
        if isinstance(img, dict): img = img.get("path")
        sid = os.path.splitext(os.path.basename(img))[0]
        w, h = Image.open(img if os.path.exists(img) else os.path.join(a.data, "images", os.path.basename(img))).size
        tampered, boxes = parse(resp)
        m = np.zeros((h, w), np.float32)
        for x1, y1, x2, y2 in boxes:
            if a.norm1000: x1, x2, y1, y2 = x1 / 1000 * w, x2 / 1000 * w, y1 / 1000 * h, y2 / 1000 * h
            m[max(0, int(y1)):int(y2), max(0, int(x1)):int(x2)] = 1.0
        if tampered and not boxes: m[:] = 0.5   # says tampered but no location: counts for detection, ~0 for localization
        np.save(os.path.join(a.out, sid + ".npy"), m); n += 1
    print("wrote", n, "maps to", a.out)


if __name__ == "__main__":
    main()
