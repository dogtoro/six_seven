"""Benchmark forgery-localization/detection models on the invoice dataset.
Usage:
  python eval_sota.py --data ../dataset_sample --models ela ext:adcdnet ext:trufor --out results --pred-root preds
Outputs: results/per_image.csv, results/summary.csv, results/summary.md, results/vis/<model>/<id>.png, results/run.log
"""
import argparse, json, logging, os, time
import numpy as np, pandas as pd
from PIL import Image
from sklearn.metrics import roc_auc_score
import models as M

THR = np.linspace(0.05, 0.95, 19)


def load_dataset(root, mask_key="mask"):
    mp = os.path.join(root, "metadata.json")
    recs = json.load(open(mp)) if os.path.exists(mp) else []
    if isinstance(recs, dict): recs = recs.get("samples", recs.get("items", list(recs.values())))
    out = []
    for r in recs:
        # tolerant to key-name differences from Zang's metadata
        img = r.get("image") or r.get("tampered") or r.get("path")
        mask = r.get(mask_key)
        label = r.get("label", 0 if (r.get("tamper_type") in (None, "none") and not mask) else 1)
        out.append(dict(id=r.get("id") or os.path.splitext(os.path.basename(img))[0], image=os.path.join(root, img),
                        mask=os.path.join(root, mask) if mask else None, label=int(label),
                        template=r.get("template", "?"), tamper_type=r.get("tamper_type", "?"),
                        compression=str(r.get("compression", r.get("qf", "?")))))
    assert out, f"no records found in {mp} (adapt load_dataset to Zang's schema)"
    return out


def prf(pred, gt):
    tp = (pred & gt).sum(); fp = (pred & ~gt).sum(); fn = (~pred & gt).sum()
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else 1.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    return iou, f1


def pixel_metrics(prob, gt):
    r = {}
    r["iou@0.5"], r["f1@0.5"] = prf(prob >= 0.5, gt)
    sc = [prf(prob >= t, gt) for t in THR]
    r["iou_oracle"] = max(s[0] for s in sc); r["f1_oracle"] = max(s[1] for s in sc)
    r["best_thr"] = float(THR[int(np.argmax([s[1] for s in sc]))])
    # stats for a dataset-level (non-oracle) dynamic threshold
    for t in THR:
        p = prob >= t
        r[f"_tp{t:.2f}"] = int((p & gt).sum()); r[f"_fp{t:.2f}"] = int((p & ~gt).sum()); r[f"_fn{t:.2f}"] = int((~p & gt).sum())
    return r


def visualize(img_path, gt, prob, out):
    img = Image.open(img_path).convert("RGB")
    heat = (np.stack([prob, prob * 0.3, 1 - prob], -1) * 255).astype(np.uint8)
    g = np.stack([gt * 255] * 3, -1).astype(np.uint8)
    h = img.size[1]; tiles = [img, Image.fromarray(g), Image.fromarray(heat)]
    canvas = Image.new("RGB", (sum(t.size[0] for t in tiles) + 20, h), (255, 255, 255)); x = 0
    for t in tiles: canvas.paste(t, (x, 0)); x += t.size[0] + 10
    os.makedirs(os.path.dirname(out), exist_ok=True); canvas.save(out)


def safe_auc(y, s):
    return roc_auc_score(y, s) if len(set(y)) == 2 else float("nan")


def det_f1(y, s):
    y, s = np.asarray(y), np.asarray(s); best = 0.0; fixed = 0.0
    for t in np.unique(np.r_[s, 0.5]):
        p = s >= t; tp = (p & (y == 1)).sum(); f = 2 * tp / (2 * tp + (p & (y == 0)).sum() + ((~p) & (y == 1)).sum() + 1e-9)
        best = max(best, f)
        if t == 0.5: fixed = f
    return fixed, best


def require_complete_predictions(model, succeeded, total):
    if succeeded != total:
        raise RuntimeError(f"{model} produced predictions for only {succeeded}/{total} samples; refusing to score a partial run")


def summarize(df, group):
    rows = []
    for key, g in ([("ALL", df)] if group is None else df.groupby(group)):
        t = g[g.label == 1]
        row = {"model": g.model.iloc[0], "group": group or "all", "value": key, "n": len(g), "n_tampered": len(t),
               "IoU@0.5": t["iou@0.5"].mean(), "F1@0.5": t["f1@0.5"].mean(),
               "IoU_oracle": t["iou_oracle"].mean(), "F1_oracle": t["f1_oracle"].mean()}
        # global dynamic threshold: pick t maximizing pooled F1 over the group's tampered images
        best = (-1, 0.5)
        for th in THR:
            tp, fp, fn = (t[f"_{k}{th:.2f}"].sum() for k in ("tp", "fp", "fn"))
            f = 2 * tp / (2 * tp + fp + fn + 1e-9); best = max(best, (f, th))
        row["F1_global_dyn"], row["global_thr"] = best
        row["det_AUC"] = safe_auc(g.label, g.score)
        row["det_F1@0.5"], row["det_F1_best"] = det_f1(g.label, g.score)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../dataset_sample"); ap.add_argument("--models", nargs="+", default=["ela"])
    ap.add_argument("--out", default="results"); ap.add_argument("--pred-root", default="preds")
    ap.add_argument("--vis", type=int, default=30, help="max visualizations per model (tampered first)")
    ap.add_argument("--mask-key", default="mask", help="metadata key of GT mask: mask (official) or mask_diff (all really-changed pixels)")
    ap.add_argument("--score", choices=["max", "top1pct"], default="max", help="image-level score from map")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", handlers=[logging.FileHandler(f"{a.out}/run.log"), logging.StreamHandler()])
    data = load_dataset(a.data, a.mask_key); logging.info("loaded %d samples from %s", len(data), a.data)
    rows = []
    for mn in a.models:
        model = M.build(mn, pred_root=a.pred_root); nvis = 0; t0 = time.time()
        before = len(rows)
        for s in data:
            try: prob = np.clip(model.predict(s["image"]), 0, 1)
            except Exception as e: logging.warning("[%s] %s failed: %s", mn, s["id"], e); continue
            h, w = prob.shape
            gt = np.asarray(Image.open(s["mask"]).convert("L").resize((w, h), Image.NEAREST)) > 127 if s["mask"] else np.zeros((h, w), bool)
            score = float(prob.max()) if a.score == "max" else float(np.sort(prob.ravel())[-max(1, prob.size // 100):].mean())
            r = dict(model=mn, id=s["id"], label=s["label"], template=s["template"], tamper_type=s["tamper_type"], compression=s["compression"], score=score)
            if s["label"] == 1: r.update(pixel_metrics(prob, gt))
            rows.append(r)
            if nvis < a.vis and s["label"] == 1: visualize(s["image"], gt, prob, f"{a.out}/vis/{mn.replace(':','_')}/{s['id']}.png"); nvis += 1
        require_complete_predictions(mn, len(rows) - before, len(data))
        logging.info("[%s] done in %.1fs", mn, time.time() - t0)
    df = pd.DataFrame(rows); df.to_csv(f"{a.out}/per_image.csv", index=False)
    parts = []
    for m, g in df.groupby("model"):
        parts += [summarize(g, grp) for grp in (None, "compression", "template", "tamper_type")]
    sm = pd.concat(parts); keep = [c for c in sm.columns if not c.startswith("_")]
    sm[keep].to_csv(f"{a.out}/summary.csv", index=False)
    open(f"{a.out}/summary.md", "w").write(sm[keep].round(3).to_markdown(index=False))
    print(sm[keep].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
