"""ADCD-Net inference on our invoice dataset -> preds/adcdnet/<id>.npy (float16 prob map at ORIGINAL image size).
ADCD-Net (github.com/KahimWong/ADCD-Net) has no inference script: main.py only logs F1 under DDP. This reuses the repo's own
GeneralValDs + ADCDNet on ONE GPU and saves the maps. UNTESTED on real weights (written against the repo code, not run on a GPU).

Prereqs: repo cloned + ds.py patched (setup_sota.sh); ADCDNet.pth, docres.pkl; qt_table.pk from the DocTamper repo
(github.com/qcf-568/DocTamper); pip: paddlepaddle paddleocr (stage prep only), jpeg2dct, lmdb, six, einops,
efficientnet_pytorch, albumentations==2.0.8, segmentation_models_pytorch.

  python adcdnet_infer.py --stage prep  --data ../dataset_sample --work work_adcd
  python adcdnet_infer.py --stage infer --data ../dataset_sample --work work_adcd --repo ../third_party/ADCD-Net \
        --ckpt ADCDNet.pth --docres docres.pkl --qt qt_table.pk --out preds/adcdnet
"""
import argparse, json, os, pickle, sys
import cv2, numpy as np


def load_records(data):
    with open(os.path.join(data, "metadata.json"), encoding="utf-8-sig") as f:
        recs = json.load(f)
    if isinstance(recs, dict): recs = recs.get("samples", recs.get("items", list(recs.values())))
    return recs


def resolve_paths(path_list, base_dir):
    """Resolve prepared paths before inference changes the working directory."""
    return [[p if os.path.isabs(p) else os.path.abspath(os.path.join(base_dir, p)) for p in row]
            for row in path_list]


def prep(a):
    """Build (img, mask, ocr_mask) triples. Authentic images get an all-black mask. OCR text masks come from PaddleOCR,
    exactly as the repo's seg_char.py does (PP-OCRv5_server_det, score>0.5, filled polygons).
    Speed: OCR runs ONCE per receipt image on its lossless __png variant and the mask is resized (nearest) for the JPEG/social variants
    (text detection is insensitive to compression); 5000 images need only 1000 OCR calls."""
    # PaddlePaddle 3.x on Windows CPU crashes in oneDNN ("ConvertPirAttribute2RuntimeAttribute not support") -> disable it
    os.environ["FLAGS_use_mkldnn"] = "0"; os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    from paddleocr import TextDetection
    try: det = TextDetection(model_name="PP-OCRv5_server_det", enable_mkldnn=False)
    except TypeError: det = TextDetection(model_name="PP-OCRv5_server_det")
    os.makedirs(f"{a.work}/masks", exist_ok=True); os.makedirs(f"{a.work}/ocr", exist_ok=True); os.makedirs(f"{a.work}/ocr_base", exist_ok=True)

    def ocr_mask(path):
        res = det.predict(input=path, batch_size=1)[0]
        h, w = cv2.imread(path).shape[:2]
        m = np.zeros((h, w), np.uint8)
        for poly, sc in zip(res["dt_polys"], res["dt_scores"]):
            if sc > 0.5: cv2.fillPoly(m, [np.asarray(poly).astype(np.int32)], 1)
        return m

    recs = load_records(a.data)
    if a.limit: recs = [r for r in recs if int(r["pair"].split("_")[1]) <= a.limit] if recs and "pair" in recs[0] else recs[:a.limit]
    triples, cache = [], {}
    for n, r in enumerate(recs):
        img_p = os.path.join(a.data, r.get("image") or r.get("tampered"))
        sid = os.path.splitext(os.path.basename(img_p))[0]
        h, w = cv2.imread(img_p).shape[:2]
        m_p = f"{a.work}/masks/{sid}.png"
        gt = cv2.imread(os.path.join(a.data, r["mask"]), 0) if r.get("mask") else np.zeros((h, w), np.uint8)
        cv2.imwrite(m_p, gt)
        base = sid.rsplit("__", 1)[0]
        png_p = os.path.join(a.data, "images", base + "__png.png")
        src_p = png_p if os.path.exists(png_p) else img_p
        key = base if src_p == png_p else sid
        if key not in cache:
            bp = f"{a.work}/ocr_base/{key}.png"
            if os.path.exists(bp): cache[key] = cv2.imread(bp, 0)            # resume support
            else:
                cache[key] = ocr_mask(src_p) * 255; cv2.imwrite(bp, cache[key])
        ocr = cache[key]
        if ocr.shape != (h, w): ocr = cv2.resize(ocr, (w, h), interpolation=cv2.INTER_NEAREST)
        o_p = f"{a.work}/ocr/{sid}.png"; cv2.imwrite(o_p, ocr)
        triples.append((img_p, m_p, o_p))
        if n % 200 == 0: print("prep", n, "/", len(recs), flush=True)
    pickle.dump(triples, open(f"{a.work}/invoices.pkl", "wb")); print("prepared", len(triples))


def infer(a):
    launch_dir = os.getcwd()
    ab = os.path.abspath                                   # resolve everything BEFORE chdir into the repo
    repo, ckpt, docres, qt, work, out = ab(a.repo), ab(a.ckpt), ab(a.docres), ab(a.qt), ab(a.work), ab(a.out)
    sys.path.insert(0, repo); os.chdir(repo)
    import torch, torch.nn.functional as F
    import cfg
    cfg.ckpt, cfg.docres_ckpt_path, cfg.qt_path, cfg.pkl_dir = ckpt, docres, qt, work
    cfg.val_max_size = a.max_size           # repo default 512: images with a longer side are DOWNSCALED
    import ds
    from model.model import ADCDNet
    dset = ds.GeneralValDs("invoices")      # reads <work>/invoices.pkl
    dset.path_list = resolve_paths(dset.path_list, launch_dir)
    model = ADCDNet().cuda().eval()
    sd = torch.load(ckpt, map_location="cpu", weights_only=True)["model"]
    model.load_state_dict({k.replace("module.", ""): v for k, v in sd.items()}, strict=True)
    os.makedirs(out, exist_ok=True)
    with torch.no_grad():
        for i in range(len(dset)):
            img, dct, qt_, mask, ocr, names, sizes = ds.pad_collate([dset[i]])
            with torch.autocast("cuda", dtype=torch.float16):
                logits = model(img.cuda(), dct.cuda(), qt_.cuda(), mask.cuda(), ocr.cuda(), is_train=False)[0]
            h, w = [int(x) for x in sizes[0]]
            prob = F.softmax(logits.float(), 1)[:, 1:2, :h, :w]          # forgery-class probability on the (resized) input
            oh, ow = cv2.imread(dset.path_list[i][0]).shape[:2]
            prob = F.interpolate(prob, size=(oh, ow), mode="bilinear", align_corners=False)[0, 0].cpu().numpy()
            np.save(os.path.join(out, names[0] + ".npy"), prob.astype(np.float16))
            if i % 20 == 0: print(i, names[0], "max=%.3f" % prob.max())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["prep", "infer"], required=True)
    p.add_argument("--data", default="../dataset_sample"); p.add_argument("--work", default="work_adcd")
    p.add_argument("--repo", default="../third_party/ADCD-Net"); p.add_argument("--ckpt", default="../third_party/weights/ADCDNet.pth")
    p.add_argument("--docres", default="../third_party/weights/docres.pkl"); p.add_argument("--qt", default="../third_party/weights/qt_table.pk")
    p.add_argument("--out", default="preds/adcdnet"); p.add_argument("--max-size", type=int, default=512)
    p.add_argument("--limit", type=int, default=0, help="prep only: first N receipts (pair ids 1..N)")
    a = p.parse_args(); {"prep": prep, "infer": infer}[a.stage](a)
