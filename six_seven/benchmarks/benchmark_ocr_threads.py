"""Time the same OCR detector at different CPU thread counts and compare masks."""
import argparse
import json
import os
import sys
from pathlib import Path
import time

parser = argparse.ArgumentParser()
parser.add_argument('--threads',type=int,required=True)
parser.add_argument('--device',default='cpu')
args = parser.parse_args()
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT'] = 'False'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
if os.environ.get('PADDLE_RUNTIME_DIR'):
    from paddle_runtime import activate
    dll_handles = activate(os.environ['PADDLE_RUNTIME_DIR'])
import cv2
import numpy as np
from paddleocr import TextDetection

root = Path(__file__).resolve().parent.parent
records = json.loads((root/'dataset_sample_v3/metadata.json').read_text(encoding='utf-8'))
samples = []
covered = set()
for r in records:
    key = (r['label'],r.get('forgery_method','none'),r['template'])
    cache = root/'benchmarks/work_adcd_v3/ocr_base'/f"{r['id'].rsplit('__',1)[0]}.png"
    if r['compression']=='png' and cache.exists() and key not in covered:
        samples.append(r)
        covered.add(key)
assert len(samples) >= 2
det = TextDetection(model_name='PP-OCRv5_server_det',enable_mkldnn=False,device=args.device,cpu_threads=args.threads)

def predict(record):
    path = str(root/'dataset_sample_v3'/record['image'])
    result = det.predict(input=path,batch_size=1)[0]
    image = cv2.imread(path)
    mask = np.zeros(image.shape[:2],np.uint8)
    for poly,score in zip(result['dt_polys'],result['dt_scores']):
        if score > .5: cv2.fillPoly(mask,[np.asarray(poly).astype(np.int32)],255)
    return mask

predict(samples[0])
timings = []
out = root/'ocr_thread_benchmark'
out.mkdir(exist_ok=True)
for record in samples:
    start = time.perf_counter()
    mask = predict(record)
    elapsed = time.perf_counter()-start
    expected = cv2.imread(str(root/'benchmarks/work_adcd_v3/ocr_base'/f"{record['id'].rsplit('__',1)[0]}.png"),0)
    equal = expected is not None and np.array_equal(mask,expected)
    np.save(out/f"{args.threads}_{record['id']}.npy",mask)
    timings.append(dict(id=record['id'],seconds=elapsed,matches_cached_mask=equal))
    print(args.threads,record['id'],round(elapsed,3),'seconds; same mask:',equal,flush=True)
(out/f"{args.device.replace(':','_')}_threads_{args.threads}.json").write_text(json.dumps(dict(device=args.device,threads=args.threads,samples=timings),indent=2))
