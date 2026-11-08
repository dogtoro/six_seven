"""Mỹ: failure analysis over teammates' DELIVERED outputs only (read-only; runs none of their code).
Inputs : benchmarks/results_v{2_annotated,3_realistic}/official_mask/{per_image.csv,vis/},
         dataset_v3_realistic/{metadata.json,authentic,tampered}, dataset_sample_v3/metadata.json, v3 fonts.
Outputs: analysis/out/*.csv + analysis/out/results.json
Run from anywhere:  python analyze_results.py
"""
import json, os, re
import numpy as np, pandas as pd, scipy.ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
from sklearn.metrics import roc_auc_score as auc

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
B = os.path.join(ROOT, "benchmarks"); V3 = os.path.join(ROOT, "dataset_v3_realistic"); OUT = os.path.join(HERE, "out")
FONTS = os.path.join(ROOT, "v3_generator_source", "thermal_receipts", "fonts")
VIS = os.path.join(B, "results_v3_realistic", "official_mask", "vis")
os.makedirs(OUT, exist_ok=True)
NEURAL = {"ext:trufor": "TruFor", "ext:adcdnet": "ADCD-Net 512", "ext:adcdnet_2048": "ADCD-Net full-res"}
COMPS = ["png", "jpeg95", "jpeg85", "jpeg75", "social_sim"]
RES = {}
rng = np.random.default_rng(20261108)


def load(rel):
    d = pd.read_csv(os.path.join(B, rel, "official_mask", "per_image.csv"), low_memory=False)
    d["pair"] = d.id.str.extract(r"(receipt_\d+)")
    return d


def cluster_ci(g, fn, n=500):
    """95% bootstrap CI resampling RECEIPTS, because the 5 variants of a receipt are not independent."""
    by = {p: x for p, x in g.groupby("pair")}; keys = list(by); vals = []
    for _ in range(n):
        vals.append(fn(pd.concat([by[k] for k in rng.choice(keys, len(keys))])))
    return [float(v) for v in np.percentile(vals, [2.5, 97.5])]


def a_uc(g): return auc(g.label, g.score) if g.label.nunique() == 2 else np.nan


# --- 1. garble audit: does each forged field look like its intended string? --------------------
def fnt(field):
    if field == "grand_total": return ImageFont.truetype(os.path.join(FONTS, "DejaVuSansMono-Bold.ttf"), 23)
    if field in ("subtotal", "vat"): return ImageFont.truetype(os.path.join(FONTS, "DejaVuSansMono.ttf"), 16)
    return ImageFont.truetype(os.path.join(FONTS, "DejaVuSansMono.ttf"), 15)


def legibility(gray, bbox, text, field):
    """Best normalised correlation between the region and a clean render of the digits (currency suffix ignored, wide search)."""
    text = text[:-2] if text.endswith(" đ") else text
    f = fnt(field); l, t, r, b = f.getbbox(text); w, h = r - l, b - t
    tpl = Image.new("L", (w, h), 255); ImageDraw.Draw(tpl).text((-l, -t), text, fill=20, font=f); tpl = np.asarray(tpl, float)
    x0, y0, x1, y1 = [int(v) for v in bbox]; best = -1.0
    for dy in range(max(0, y0 - 4), y1 + 5 - h + 1):
        for dx in range(max(0, x0 - 8), max(x0 - 7, x1 + 8 - w) + 1):
            c = gray[dy:dy + h, dx:dx + w]
            if c.shape != tpl.shape or c.std() < 1 or tpl.std() < 1: continue
            best = max(best, float(np.corrcoef(c.ravel(), tpl.ravel())[0, 1]))
    return best


meta = json.load(open(os.path.join(V3, "metadata.json"), encoding="utf-8"))
mt = pd.DataFrame(meta).set_index("sample_id")
mt["filter"] = mt.forgery_detail.map(lambda x: (x or {}).get("patch_filter"))
mt["sub"] = mt.forgery_detail.map(lambda x: (x or {}).get("double_jpeg_submethod"))
mt["copy_based"] = (mt.forgery_method == "copy_move") | (mt["sub"] == "copy_move")
rows = []
for r in meta:
    s = r["sample_id"]
    A = np.asarray(Image.open(f"{V3}/authentic/{s}_authentic.png").convert("L"), float)
    T = np.asarray(Image.open(f"{V3}/tampered/{s}_tampered.png").convert("L"), float)
    for tf in r["tampered_fields"]:
        fld = re.sub(r"item_\d+_", "item_", tf["field"])
        rows.append(dict(sid=s, method=r["forgery_method"], copy_based=bool(mt.loc[s, "copy_based"]), field=fld,
                         control=legibility(A, tf["bbox"], tf["original"], fld), forged=legibility(T, tf["bbox"], tf["forged"], fld)))
L = pd.DataFrame(rows)
# Paired rule: V2 text was rendered with slightly different font files, so each field is compared with ITS OWN authentic control.
L["garbled"] = L.forged < L.control - 0.15
L.to_csv(f"{OUT}/legibility_fields.csv", index=False)
gar_tab = L.groupby(["field", "copy_based"]).agg(n=("garbled", "size"), garbled=("garbled", "mean"), control=("control", "median"), forged=("forged", "median")).round(3)
gar_tab.to_csv(f"{OUT}/legibility_summary.csv"); print(gar_tab)
gar_receipts = set(L[L.garbled & L.copy_based].sid)
print(L.groupby("method").garbled.mean().round(3).to_dict(), "garbled receipts among copy-based:", len(gar_receipts))
RES["garbled_receipts"] = len(gar_receipts); RES["copy_based_receipts"] = int(mt.copy_based.sum())
RES["garbled_by_method"] = L.groupby("method").garbled.mean().round(4).to_dict()
RES["garbled_noncopy_receipts"] = len(set(L[L.garbled & ~L.copy_based].sid))
flagged = gar_receipts   # only copy-based counts as invalid: another font scoring low is the forgery working as designed
pd.Series(sorted(flagged), name="sample_id").to_csv(f"{OUT}/receipts_garbled.csv", index=False)

# --- 2. V3 metrics ---------------------------------------------------------------------------
v3 = load("results_v3_realistic")
for c in ("forgery_method", "tamper_type", "template"): pass
v3["method"] = v3.pair.map(mt.forgery_method); v3["filter"] = v3.pair.map(mt["filter"]); v3["ttype"] = v3.pair.map(mt.tamper_type)
v3["valid"] = ~v3.pair.isin(flagged)
RES["valid_receipts"] = int(v3[v3.valid].pair.nunique())
rows = []
for mn, name in NEURAL.items():
    g = v3[v3.model == mn]; t = g[g.label == 1]
    for sub_name, x in (("all 300", g), ("legible only", g[g.valid])):
        xt = x[x.label == 1]; a, f = x[x.label == 0].score, xt.score
        rows.append(dict(model=name, subset=sub_name, receipts=x.pair.nunique(), AUC=a_uc(x), AUC_lo=cluster_ci(x, a_uc)[0], AUC_hi=cluster_ci(x, a_uc)[1],
                         F1_05=xt["f1@0.5"].mean(), F1_oracle=xt.f1_oracle.mean(), F1_median=xt["f1@0.5"].median(), share_F1_lt_01=(xt["f1@0.5"] < .01).mean(), share_F1_ge_05=(xt["f1@0.5"] >= .5).mean(),
                         TPR_at_05=(f >= .5).mean(), FPR_at_05=(a >= .5).mean(), TPR_at_FPR5=(f >= a.quantile(.95)).mean()))
head = pd.DataFrame(rows); head.to_csv(f"{OUT}/headline.csv", index=False); print(head.round(3).to_string())


def by(grp, valid_only):
    out = []
    for mn, name in NEURAL.items():
        g = v3[v3.model == mn]
        if valid_only: g = g[g.valid]
        for k, x in g.groupby(grp):
            xt = x[x.label == 1]
            if not len(xt): continue
            out.append(dict(model=name, **{grp: k}, n_receipts=x.pair.nunique(), AUC=a_uc(x), F1_05=xt["f1@0.5"].mean(), F1_oracle=xt.f1_oracle.mean()))
    return pd.DataFrame(out)


for grp in ("method", "compression", "ttype"):
    for vo in (False, True):
        t = by(grp, vo); t.to_csv(f"{OUT}/by_{grp}{'_legible' if vo else ''}.csv", index=False)
print(by("method", True).round(3).to_string()); print(by("compression", True).round(3).to_string()); print(by("ttype", True).round(3).to_string())
fl = by("filter", False); fl.to_csv(f"{OUT}/by_filter.csv", index=False); print(fl.round(3).to_string())

# like-for-like V2 -> V3 on same receipts, same (map-max) score, same 512 cap for ADCD
v2 = load("results_v2_annotated"); out = []
for mn in ("ext:trufor", "ext:adcdnet"):
    a = v2[(v2.model == mn) & v2.pair.isin(set(v3.pair))]; b = v3[(v3.model == mn)]
    out.append(dict(model=NEURAL[mn], V2_AUC=auc(a.label, a.score), V3_AUC_mapmax=auc(b.label, b.prob_max), V3_AUC_reported=auc(b.label, b.score),
                    V2_F1=a[a.label == 1]["f1@0.5"].mean(), V3_F1=b[b.label == 1]["f1@0.5"].mean(), V2_oracle=a[a.label == 1].f1_oracle.mean(), V3_oracle=b[b.label == 1].f1_oracle.mean()))
pd.DataFrame(out).to_csv(f"{OUT}/v2_vs_v3.csv", index=False); print(pd.DataFrame(out).round(3).to_string())

# resize sensitivity: tall supermarket receipts are the only images 1024 and 2048 treat differently
hh = v3[(v3.label == 1) & (v3.template == "supermarket") & v3.model.isin(["ext:adcdnet_1024", "ext:adcdnet_2048"])].copy()
hh["tall"] = hh.pair.map(mt.height) > 1024
rs = hh.pivot_table(index=["tall", "compression"], columns="model", values="f1@0.5"); rs.to_csv(f"{OUT}/resize_sensitivity.csv"); print(rs.round(3))
RES["tall_receipts"] = int((mt.height > 1024).sum())

# --- 3. arithmetic check from metadata alone (perfect-OCR upper bound) --------------------------
def num(s): return int(re.sub(r"[^\d]", "", s))


rows = []
for r in meta:
    d = {re.sub(r"item_\d+_", "item_", f["field"]): num(f["forged"]) - num(f["original"]) for f in r["tampered_fields"]}
    q = d.get("item_total", 0); sub = d.get("subtotal", 0); vat = d.get("vat", 0); gt = d.get("grand_total", 0)
    # Authentic receipts satisfy: Σitems = subtotal, subtotal - discount + VAT = total. The edits shift each side by these deltas:
    broke_sum = q != sub; broke_total = gt != sub + vat
    rows.append(dict(sid=r["sample_id"], tamper_type=r["tamper_type"], broke_sum=broke_sum, broke_total=broke_total, inconsistent=broke_sum or broke_total))
AR = pd.DataFrame(rows); ar_tab = AR.groupby("tamper_type").agg(receipts=("sid", "size"), inconsistent=("inconsistent", "mean")); print(ar_tab)
ar_tab.to_csv(f"{OUT}/arith_by_type.csv")
RES["arith_recall"] = float(AR.inconsistent.mean())
incons = set(AR[AR.inconsistent].sid)
rows = []
for scope, keep in (("all 300", lambda x: x), ("legible", lambda x: x[x.valid])):
    for mn, name in NEURAL.items():
        g = keep(v3[v3.model == mn]); a = g[g.label == 0]; t = g[g.label == 1]; thr = a.score.quantile(.95)
        pix = t.score >= thr; sem = t.pair.isin(incons)
        rows.append(dict(scope=scope, model=name, threshold=thr, receipts=t.pair.nunique(), pixel_TPR=pix.mean(), arith_TPR=sem.mean(), combined_TPR=(pix | sem).mean(), FPR=(a.score >= thr).mean()))
fus = pd.DataFrame(rows); fus.to_csv(f"{OUT}/fusion.csv", index=False); print(fus.round(3).to_string())
# worst case: the receipt still adds up AND no post-filter AND digits legible. Only pixel evidence could catch it.
rows = []
for mn, name in NEURAL.items():
    g = v3[v3.model == mn]; thr = g[g.label == 0].score.quantile(.95); t = g[(g.label == 1)].copy()
    t["cue"] = np.select([t.pair.isin(flagged), t["filter"].isin(["blur", "sharpen"])], ["garbled digits", "post-filter"], "clean edit")
    for (ty, cue), x in t.groupby([t.ttype == "full_financial", "cue"]):
        rows.append(dict(model=name, arith_consistent=bool(ty), cue=cue, receipts=x.pair.nunique(), pixel_TPR_at_FPR5=(x.score >= thr).mean(), F1=x["f1@0.5"].mean()))
    for cue, x in t.groupby("cue"):
        y = pd.concat([x, g[(g.label == 0) & g.pair.isin(set(x.pair))]])
        rows.append(dict(model=name, arith_consistent="any", cue=cue, receipts=x.pair.nunique(), pixel_TPR_at_FPR5=(x.score >= thr).mean(), F1=x["f1@0.5"].mean(), AUC=a_uc(y), AUC_lo=cluster_ci(y, a_uc)[0], AUC_hi=cluster_ci(y, a_uc)[1]))
cue = pd.DataFrame(rows); cue.to_csv(f"{OUT}/by_cue.csv", index=False); print(cue.round(3).to_string())

# --- 4. heatmap panels: failure taxonomy (tile = image | mask | heat; heat red channel = prob) -----
smeta = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "dataset_sample_v3", "metadata.json"), encoding="utf-8"))}


def tiles(path):
    im = np.asarray(Image.open(path).convert("RGB")).astype(float); w = (im.shape[1] - 20) // 3
    return im[:, :w], im[:, 2 * (w + 10):2 * (w + 10) + w, 0] / 255


def fp_types(img, flag):
    """Label each flagged blob by what it sits on: printer streak, text, or blank paper."""
    res = dict(streak=0, text=0, blank=0)
    text = ndi.binary_dilation(img.mean(-1) < 140, iterations=2)
    lab, n = ndi.label(flag)
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start; blob = lab[sl] == i
        if blob.sum() < 12: continue
        if h >= 40 and h >= 4 * w: res["streak"] += 1
        elif text[sl][blob].mean() >= .3: res["text"] += 1
        else: res["blank"] += 1
    return res


fld, img_rows = [], []
for mn in ("ext_trufor", "ext_adcdnet", "ext_adcdnet_2048"):
    for f in sorted(os.listdir(f"{VIS}/{mn}")):
        if "_tampered__" not in f: continue
        tid = f[:-4]; aid = tid.replace("_tampered__", "_authentic__"); r = smeta[tid]; pair = r["pair"]
        It, Ht = tiles(f"{VIS}/{mn}/{f}"); Ia, Ha = tiles(f"{VIS}/{mn}/{aid}.png"); K = np.zeros(Ht.shape, bool)
        for tf in r["tampered_fields"]:
            x0, y0, x1, y1 = [int(v) for v in tf["bbox"]]; K[y0:y1 + 1, x0:x1 + 1] = True
            pt, pa = Ht[y0:y1 + 1, x0:x1 + 1], Ha[y0:y1 + 1, x0:x1 + 1]
            fld.append(dict(model=mn, field=re.sub(r"item_\d+_", "item_", tf["field"]), pair=pair, valid=pair not in flagged, tampered=(pt >= .5).mean(), authentic=(pa >= .5).mean()))
        Ft, Fa = Ht >= .5, Ha >= .5; tp = (Ft & K).sum(); pred = Ft.sum(); rec = tp / K.sum(); prec = tp / pred if pred else 0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        # tampered-panel category (fixed rule, no labels tuned)
        if f1 >= .5: cat = "hit"
        elif rec >= .05 and tp >= (Ft & ~K).sum(): cat = "partial"
        elif (Ft & ~K).sum() > tp and rec < .05: cat = "misplaced" if pred >= 12 else "silent miss"
        elif rec >= .05: cat = "partial+noise"
        else: cat = "silent miss"
        fp = fp_types(Ia, Fa)
        img_rows.append(dict(model=mn, pair=pair, tid=tid, method=r["forgery_method"], compression=r["compression"], valid=pair not in flagged, cat=cat, f1=f1, recall=rec,
                             auth_flagged=bool(Fa.sum() >= 12), **{f"fp_{k}": v for k, v in fp.items()}))
F = pd.DataFrame(fld); P = pd.DataFrame(img_rows); P.to_csv(f"{OUT}/panel_taxonomy.csv", index=False)
ft = F[F.valid].groupby(["model", "field"]).agg(n=("tampered", "size"), tampered=("tampered", "mean"), authentic=("authentic", "mean")); ft.to_csv(f"{OUT}/field_response.csv"); print(ft.round(3))
ct = pd.crosstab(P[P.valid].model, P[P.valid].cat, normalize="index"); ct.to_csv(f"{OUT}/taxonomy_tampered.csv"); print(ct.round(3)); print(P[P.valid].groupby("model").size())
fpt = P[P.valid].groupby("model").agg(pairs=("pair", "size"), authentic_with_false_alarm=("auth_flagged", "mean"), streak=("fp_streak", lambda x: (x > 0).mean()), text=("fp_text", lambda x: (x > 0).mean()), blank=("fp_blank", lambda x: (x > 0).mean()))
fpt.to_csv(f"{OUT}/taxonomy_authentic.csv"); print(fpt.round(3))
json.dump(RES, open(f"{OUT}/results.json", "w"), indent=1); print(RES)
