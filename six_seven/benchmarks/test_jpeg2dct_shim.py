"""Check the pure-Python jpeg2dct stand-in against jpegio (true libjpeg coefficients).  pip install jpegio   (Linux/mac; optional)
python test_jpeg2dct_shim.py [image]"""
import glob, os, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "third_party", "ADCD-Net"))
from jpeg2dct.numpy import load
import jpegio

src = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "dataset_raw", "tampered", "*.png")))[0]
im = Image.open(src).convert("L")
for qf in (100, 90, 75):
    for crop in ((0, 0, im.size[0], im.size[1]), (0, 0, im.size[0] - 3, im.size[1] - 5)):   # also a non-multiple-of-8 size
        f = os.path.join(tempfile.gettempdir(), "shim_t.jpg"); im.crop(crop).save(f, "JPEG", quality=qf)
        mine = load(f)[0]
        jp = jpegio.read(f); ref = np.array(jp.coef_arrays[0], copy=True); R, C = ref.shape[0] // 8, ref.shape[1] // 8
        ref = ref.reshape(R, 8, C, 8).transpose(0, 2, 1, 3).reshape(R, C, 64)
        d = np.abs(mine.astype(int) - ref.astype(int))
        print(f"qf={qf} size={crop[2:]} shape_ok={mine.shape == ref.shape} exact={100 * (d == 0).mean():.2f}% max_abs_diff={d.max()} diff>1: {(d > 1).sum()}")
