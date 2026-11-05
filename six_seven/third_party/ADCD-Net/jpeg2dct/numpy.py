"""Drop-in replacement for `from jpeg2dct.numpy import load` used by ADCD-Net's ds.py.
Returns (dct_y, None, None); dct_y has shape [H/8, W/8, 64] holding the QUANTIZED luma DCT coefficients in natural (row-major) order
inside each 8x8 block, like libjpeg.  Computed by re-DCT of the decoded pixels and dividing by the file's quantization table, so it
can differ from libjpeg's exact coefficients by +-1 where decoder rounding/clipping matters (small at QF 100, which is what ADCD-Net
inference uses). Validated against jpegio (true libjpeg coefficients) in six_seven/benchmarks/test_jpeg2dct_shim.py."""
import numpy as np
from PIL import Image
from scipy.fft import dctn

def _qtable_natural(im):
    # Pillow already returns the table in natural (row-major) order (verified against jpegio)
    return np.array(im.quantization[0], dtype=np.float64).reshape(8, 8)


def load(path, normalized=False):
    im = Image.open(path)
    q = _qtable_natural(im)
    y = np.asarray(im if im.mode == "L" else im.convert("YCbCr").getchannel(0), dtype=np.float64)
    im.close()
    h, w = y.shape
    ph, pw = (-h) % 8, (-w) % 8
    if ph or pw: y = np.pad(y, ((0, ph), (0, pw)), mode="edge")                # encoder pads by edge replication
    H, W = y.shape
    blocks = y.reshape(H // 8, 8, W // 8, 8).transpose(0, 2, 1, 3) - 128.0
    coef = dctn(blocks, axes=(2, 3), norm="ortho")
    quant = np.rint(coef / q).astype(np.int16)
    if normalized: quant = (quant * q).astype(np.float32)
    return quant.reshape(H // 8, W // 8, 64), None, None
