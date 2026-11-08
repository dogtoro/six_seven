"""Audit every generated V3 pair before model inference."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parent.parent
raw = root / 'dataset_v3_realistic'
records = json.loads((raw / 'metadata.json').read_text(encoding='utf-8'))
manifest = [json.loads(s) for s in (raw / 'manifest.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
assert records == manifest
assert len(records) == len({r['sample_id'] for r in records}) == 300
assert set(Counter(r['template'] for r in records).values()) == {75}
assert Counter(r['forgery_method'] for r in records) == dict.fromkeys(['copy_move','splice_font','splice_same_font','double_jpeg'],75)
source_hashes = json.loads((root / 'dataset_v3_source_hashes.json').read_text())
assert set(source_hashes) == {r['sample_id'] for r in records}
for r in records:
    a_path = raw / r['authentic_file']
    assert hashlib.sha256(a_path.read_bytes()).hexdigest() == source_hashes[r['sample_id']]
    a = np.array(Image.open(a_path).convert('RGB'))
    t = np.array(Image.open(raw / r['tampered_file']).convert('RGB'))
    mask = np.array(Image.open(raw / r['mask_file']).convert('L')) > 0
    assert a.shape == t.shape and a.shape[:2] == mask.shape
    diff = np.any(a != t, axis=-1)
    assert diff.any() and not (diff & ~mask).any(), r['sample_id']
    assert int(mask.sum()) == r['mask_px'] and int(diff.sum()) == r['diff_px']
report = dict(pairs=300, expected_benchmark_images=3000, changed_pixels_outside_masks=0,
              authentic_images_byte_identical_to_v2=True, methods=dict(Counter(r['forgery_method'] for r in records)),
              provenance='v3_generation_provenance.json')
(root / 'dataset_v3_audit.json').write_text(json.dumps(report,indent=2))
prepared = root/'dataset_sample_v3'
if (prepared/'metadata.json').exists():
    samples = json.loads((prepared/'metadata.json').read_text(encoding='utf-8'))
    assert len(samples) == len({s['id'] for s in samples}) == 3000
    assert {s['pair'] for s in samples} == {r['sample_id'] for r in records}
    assert Counter(s['compression'] for s in samples) == dict.fromkeys(['png','jpeg95','jpeg85','jpeg75','social_sim'],600)
    for s in samples:
        assert (prepared/s['image']).is_file()
        if s['label']:
            assert (prepared/s['mask']).is_file() and (prepared/s['mask_diff']).is_file()
    print('PASS: existing 3000 prepared records, images and masks are available for reuse')
print('PASS: 300 V3 pairs; byte-identical authentic sources; strict RGB diff covered by mask; balanced methods/templates')
