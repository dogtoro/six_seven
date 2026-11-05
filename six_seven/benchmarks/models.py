"""Model adapters. Each adapter: predict(path) -> float32 HxW prob map in [0,1] (same size as input).
Register new ones in REGISTRY. For models that are painful to import (ADCD-Net, TruFor, TextShield-R1)
use ExternalMaps: run each repo's own inference script, dump maps to preds/<model>/<id>.(png|npy), then evaluate.
"""
import io, os
import numpy as np
from PIL import Image, ImageChops


class ELABaseline:
    """Sanity-check baseline (Error Level Analysis). Not a SOTA; shows what a trivial detector scores."""
    name = "ela"
    def __init__(self, qf=90, **_): self.qf = qf
    def predict(self, path):
        im = Image.open(path).convert("RGB"); buf = io.BytesIO(); im.save(buf, "JPEG", quality=self.qf)
        diff = np.asarray(ImageChops.difference(im, Image.open(buf).convert("RGB")), np.float32).max(-1)
        return np.clip(diff / (diff.max() + 1e-6), 0, 1)


class RandomBaseline:
    name = "random"
    def __init__(self, seed=0, **_): self.rng = np.random.default_rng(seed)
    def predict(self, path):
        w, h = Image.open(path).size; return self.rng.random((h, w)).astype(np.float32)


class ExternalMaps:
    """Reads precomputed maps: <pred_root>/<model_name>/<sample_id>.png|.npy|.npz  (png: 0-255 -> 0-1; npz: TruFor, key 'map')."""
    def __init__(self, name, pred_root="preds", **_): self.name = name; self.root = os.path.join(pred_root, name)
    def predict(self, path):
        sid = os.path.splitext(os.path.basename(path))[0]
        import glob
        cands = [(".npy", os.path.join(self.root, sid + ".npy")), (".npz", os.path.join(self.root, sid + ".npz")), (".png", os.path.join(self.root, sid + ".png"))]
        cands += [(".npz", f) for f in glob.glob(os.path.join(self.root, sid + ".*.npz"))]   # TruFor names outputs <image filename>.npz, e.g. x.jpg.npz
        for ext, f in cands:
            if os.path.exists(f):
                if ext == ".npy": m = np.load(f)
                elif ext == ".npz": m = np.load(f)["map"]          # TruFor output: keys map, conf, score
                else: m = np.asarray(Image.open(f).convert("L"), np.float32) / 255.0
                return m.astype(np.float32)
        raise FileNotFoundError(f"no prediction for {sid} in {self.root}")


class ADCDNet:
    """Direct adapter. Fill in after cloning the repo (see setup_adcdnet.sh). The repo's exact entry points
    must be checked on your clone; this wrapper isolates that to ONE place (_load / _infer)."""
    name = "adcdnet"
    def __init__(self, repo="third_party/ADCD-Net", ckpt="ADCDNet.pth", docres="docres.pkl", device="cuda:0", **_):
        self.repo, self.ckpt, self.docres, self.device = repo, ckpt, docres, device
        self._load()
    def _load(self):
        raise NotImplementedError("Open the ADCD-Net repo's test/inference script, import its model builder here, "
                                  "load ADCDNet.pth + docres.pkl. Or use ExternalMaps: run repo inference, save maps to preds/adcdnet/.")
    def predict(self, path): raise NotImplementedError


REGISTRY = {"ela": ELABaseline, "random": RandomBaseline, "adcdnet": ADCDNet}


def build(name, **kw):
    if name in REGISTRY: return REGISTRY[name](**kw)
    if name.startswith("ext:"): return ExternalMaps(name[4:], **kw)   # e.g. ext:trufor, ext:adcdnet
    raise KeyError(name)
