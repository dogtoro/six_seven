"""Report figures from analysis/out/*.csv and teammates' published heatmap panels (read-only)."""
import os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out"); FIG = os.path.join(OUT, "figures"); os.makedirs(FIG, exist_ok=True)
VIS = os.path.join(ROOT, "benchmarks", "results_v3_realistic", "official_mask", "vis")
V3 = os.path.join(ROOT, "dataset_v3_realistic")
MODELS = ["TruFor", "ADCD-Net 512", "ADCD-Net full-res"]
COL = {"TruFor": "#2a78d6", "ADCD-Net 512": "#eb6834", "ADCD-Net full-res": "#1baf7a"}   # validated default palette, fixed order
MARK = {"TruFor": "o", "ADCD-Net 512": "s", "ADCD-Net full-res": "D"}                    # identity is never colour alone
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})


def fig_cue():
    d = pd.read_csv(f"{OUT}/by_cue.csv"); d = d[d.arith_consistent == "any"]
    order = ["clean edit", "post-filter", "garbled digits"]
    lab = {"clean edit": "Clean edit\n(no filter, legible)", "post-filter": "Same font +\nblur / sharpen", "garbled digits": "Garbled digits\n(generator defect)"}
    fig, ax = plt.subplots(figsize=(7.2, 3.3)); w = .24
    for i, m in enumerate(MODELS):
        x = d[d.model == m].set_index("cue").loc[order]; pos = np.arange(3) + (i - 1) * w
        ax.bar(pos, x.AUC - .5, w - .03, bottom=.5, color=COL[m], label=m)
        ax.errorbar(pos, x.AUC, yerr=[x.AUC - x.AUC_lo, x.AUC_hi - x.AUC], fmt="none", ecolor=INK2, lw=1, capsize=2)
        for p, v, hi in zip(pos, x.AUC, x.AUC_hi): ax.text(p, hi + .012, f"{v:.2f}", ha="center", fontsize=8.5, color=INK)
    ax.axhline(.5, color=INK2, lw=1); ax.text(-.47, .505, "chance", fontsize=8.5, color=INK2, ha="left")
    ax.set_xlim(-.5, 2.5); ax.set_xticks(range(3), [lab[o] for o in order]); ax.set_ylim(.45, 1.03); ax.set_ylabel("Detection AUC"); ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{FIG}/fig1_auc_by_cue.png", dpi=170); plt.close(fig)


def fig_comp():
    d = pd.read_csv(f"{OUT}/by_compression_legible.csv"); order = ["png", "jpeg95", "jpeg85", "jpeg75", "social_sim"]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for ax, col, ttl in ((axs[0], "AUC", "Detection AUC"), (axs[1], "F1_05", "Localization F1@0.5")):
        for m in MODELS:
            x = d[d.model == m].set_index("compression").loc[order]
            ax.plot(order, x[col], color=COL[m], lw=2, marker=MARK[m], ms=6, mec="#fcfcfb", label=m)
        ax.set_title(ttl, fontsize=10, loc="left", color=INK); ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0, axis="both"); ax.tick_params(axis="x", labelsize=8.5)
    axs[0].axhline(.5, color=INK2, lw=1); axs[0].set_ylim(.45, .8); axs[1].set_ylim(0, .25)
    axs[0].legend(frameon=False, fontsize=8.5, loc="upper right")
    fig.tight_layout(); fig.savefig(f"{FIG}/fig2_compression.png", dpi=170); plt.close(fig)


def label(im, text):
    W, H = im.size; c = Image.new("RGB", (W, H + 26), "#fcfcfb"); c.paste(im, (0, 26))
    ImageDraw.Draw(c).text((4, 5), text, fill=INK, font=ImageFont.truetype(os.path.join(ROOT, "v3_generator_source", "thermal_receipts", "fonts", "LiberationSans-Bold.ttf"), 15))
    return c


def panel(model, sid, y0=0, y1=None, title=""):
    im = Image.open(f"{VIS}/{model}/{sid}.png").convert("RGB"); W, H = im.size; w = (W - 20) // 3
    im = im.crop((0, y0, W, y1 or H)); return label(im, title)


def fig_panels():
    t = pd.read_csv(f"{OUT}/panel_taxonomy.csv"); pick = {}
    ad = t[(t.model == "ext_adcdnet_2048") & t.valid]
    # data-driven picks: clearest example of each failure, png preferred where the cell exists
    pf = ad[(ad.method == "splice_font") & (ad["cat"] == "silent miss")].sort_values(["compression"]).iloc[0]
    pick["miss"] = pf.tid
    a = "receipt_0001_authentic__jpeg75"; b = "receipt_0001_tampered__jpeg75"
    rows = [panel("ext_trufor", a, 0, 960, "A. TruFor on an AUTHENTIC receipt: fires on a bold header and a printer streak"),
            panel("ext_adcdnet_2048", b, 0, 720, "B. ADCD-Net full-res, same receipt forged (same font + sharpen): localizes the edits"),
            panel("ext_adcdnet_2048", pick["miss"], 0, 720, f"C. ADCD-Net full-res, wrong-font edit ({pick['miss'][8:12]}, {pf.compression}): nothing flagged")]
    W = max(r.width for r in rows); H = sum(r.height for r in rows) + 12; O = Image.new("RGB", (W, H), "#fcfcfb"); y = 0
    for r in rows: O.paste(r, (0, y)); y += r.height + 6
    O = O.resize((int(O.width * .5), int(O.height * .5)), Image.LANCZOS); O.save(f"{FIG}/fig3_panels.png"); print(pick, O.size)


def fig_garble():
    import json; M = {r["sample_id"]: r for r in json.load(open(f"{V3}/metadata.json", encoding="utf-8"))}
    ids = ["receipt_0005", "receipt_0148", "receipt_0280", "receipt_0032"]; rows = []
    for s in ids:
        A = Image.open(f"{V3}/authentic/{s}_authentic.png").convert("RGB"); T = Image.open(f"{V3}/tampered/{s}_tampered.png").convert("RGB")
        f = [x for x in M[s]["tampered_fields"] if x["field"] == "grand_total"][0]; b = f["bbox"]; box = (max(0, b[0] - 40), b[1] - 5, min(A.width, b[2] + 40), b[3] + 5)
        c = Image.new("RGB", (2 * (box[2] - box[0]) + 12, box[3] - box[1]), "#d03b3b"); c.paste(A.crop(box), (0, 0)); c.paste(T.crop(box), (box[2] - box[0] + 12, 0)); rows.append(c)
    W = max(r.width for r in rows); O = Image.new("RGB", (W, sum(r.height + 4 for r in rows)), "#fcfcfb"); y = 0
    for r in rows: O.paste(r, (0, y)); y += r.height + 4
    O.save(f"{FIG}/fig4_garbled.png"); print(O.size)


if __name__ == "__main__":
    fig_cue(); fig_comp(); fig_panels(); fig_garble()
