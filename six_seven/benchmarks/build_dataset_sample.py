"""Turn Zang's raw folders (authentic/ tampered/ masks/, PNG, optional metadata) into dataset_sample/ with compression variants + metadata.json.
  python build_dataset_sample.py --raw /path/dataset_grpprj_himladro_2026 --out ../dataset_sample [--limit N]
Variants (deterministic): png (lossless original), jpeg95, jpeg85, jpeg75, social_sim (resize x0.75 bicubic -> JPEG q70; a SIMULATION, not real Zalo/Messenger).
Two ground truths per tampered image:
  mask       = Zang's official mask (edited fields only)
  mask_diff  = every pixel that really differs between authentic and tampered (dilated 2px), may differ from the official bounding-box mask even when that mask covers every changed pixel.
"""
import argparse, io, json, os
import numpy as np, scipy.ndimage as ndi
from PIL import Image

VARIANTS = ["png", "jpeg95", "jpeg85", "jpeg75", "social_sim"]


def save_variant(im, mask, v, base, out):
    """returns (image_rel, mask_rel_or_None-transformer). Writes image; mask resized for social_sim."""
    if v == "social_sim":
        w, h = im.size; im = im.resize((int(w * .75), int(h * .75)), Image.BICUBIC)
        if mask is not None: mask = mask.resize(im.size, Image.NEAREST)
    if v == "png": rel = f"images/{base}__png.png"; im.save(f"{out}/{rel}")
    else:
        q = {"jpeg95": 95, "jpeg85": 85, "jpeg75": 75, "social_sim": 70}[v]
        rel = f"images/{base}__{v}.jpg"; im.save(f"{out}/{rel}", "JPEG", quality=q)
    return rel, mask


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--out", default="../dataset_sample"); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    for d in ("images", "masks", "masks_diff"): os.makedirs(f"{a.out}/{d}", exist_ok=True)
    ids = sorted(f.split("_")[1] for f in os.listdir(f"{a.raw}/authentic")); ids = ids[:a.limit] if a.limit else ids
    meta_path = os.path.join(a.raw, "metadata.json")
    meta_map = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8-sig") as f:
            meta_map = {m["sample_id"]: m for m in json.load(f)}
    recs = []
    for k in ids:
        A = Image.open(f"{a.raw}/authentic/receipt_{k}_authentic.png").convert("RGB")
        T = Image.open(f"{a.raw}/tampered/receipt_{k}_tampered.png").convert("RGB")
        M = Image.open(f"{a.raw}/masks/receipt_{k}_mask.png").convert("L").point(lambda p: 255 if p > 0 else 0)
        assert A.size == T.size == M.size, k
        m = np.array(M) > 0; d = (np.abs(np.array(A).astype(int) - np.array(T).astype(int)).sum(-1) > 0)
        MD = Image.fromarray((ndi.binary_dilation(d, iterations=2) * 255).astype(np.uint8))
        lab, n = ndi.label(m); boxes = [[int(s[1].start), int(s[0].start), int(s[1].stop), int(s[0].stop)] for s in ndi.find_objects(lab)]
        sample_meta = meta_map.get(f"receipt_{k}", {})
        layout = sample_meta.get("template", "unknown")
        tamper_type = sample_meta.get("tamper_type", "unknown")
        for v in VARIANTS:
            ra, _ = save_variant(A, None, v, f"receipt_{k}_authentic", a.out)
            rt, m2 = save_variant(T, M, v, f"receipt_{k}_tampered", a.out)
            _, md2 = save_variant(T, MD, v, f"tmp_{k}", a.out); os.remove(f"{a.out}/images/tmp_{k}__{v}." + ("png" if v == "png" else "jpg"))
            mr = f"masks/receipt_{k}_{v}.png"; m2.save(f"{a.out}/{mr}"); mdr = f"masks_diff/receipt_{k}_{v}.png"; md2.save(f"{a.out}/{mdr}")
            common = dict(pair=f"receipt_{k}", template=layout, compression=v, size=list(A.size if v != "social_sim" else (int(A.size[0] * .75), int(A.size[1] * .75))))
            recs.append(dict(id=f"receipt_{k}_authentic__{v}", image=ra, mask=None, mask_diff=None, label=0, tamper_type="none", n_regions=0, **common))
            recs.append(dict(id=f"receipt_{k}_tampered__{v}", image=rt, mask=mr, mask_diff=mdr, label=1, tamper_type=tamper_type, n_regions=n,
                             tampered_fields=sample_meta.get("tampered_fields", []),
                             bbox=boxes, mask_px=int(m.sum()), diff_px=int(d.sum()), mask_covers_diff=round(float((d & m).sum() / d.sum()), 4), **common))
    json.dump(recs, open(f"{a.out}/metadata.json", "w"), indent=1)
    print("pairs", len(ids), "records", len(recs))


if __name__ == "__main__":
    main()
