"""Bundle 100 paired V3 receipts with raw probability maps and ground truth."""
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np

VARIANTS = ['png','jpeg95','jpeg85','jpeg75','social_sim']


def select_records(records, count=100):
    pairs = sorted({r['pair'] for r in records})
    if len(pairs) < count: raise ValueError('Not enough distinct receipt pairs')
    lookup = {(r['pair'],r['compression'],r['label']):r for r in records}
    chosen = [pairs[i] for i in np.linspace(0,len(pairs)-1,count,dtype=int)]
    selected = []
    for i, pair in enumerate(chosen):
        for label in [0,1]: selected.append(lookup[pair,VARIANTS[i % len(VARIANTS)],label])
    return selected


def package():
    root = Path(__file__).resolve().parent.parent
    data = root / 'dataset_sample_v3'
    selected = select_records(json.loads((data / 'metadata.json').read_text(encoding='utf-8')))
    target = root / 'v3_failure_analysis_maps.zip'
    temporary = target.with_suffix('.zip.partial')
    manifest = []
    added = set()
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
        def add(path, name):
            if name not in added:
                archive.write(path,name)
                added.add(name)
        for record in selected:
            for field in ['image','mask','mask_diff']:
                if record.get(field): add(data / record[field], 'dataset_sample_v3/'+record[field])
            for model in ['adcdnet','adcdnet_1024','adcdnet_2048','trufor']:
                folder = root / 'benchmarks/preds_v3' / model
                path = folder / (record['id']+'.npy') if model != 'trufor' else folder / (Path(record['image']).name+'.npz')
                native = None
                if model == 'trufor':
                    with np.load(path) as values:
                        prob = values['map']
                        native = float(values['score'].item())
                        assert np.isfinite(native) and 0 <= native <= 1
                else: prob = np.load(path,mmap_mode='r')
                assert prob.shape == (record['size'][1],record['size'][0])
                assert np.isfinite(prob).all() and ((prob >= 0) & (prob <= 1)).all()
                name = 'preds_v3/'+model+'/'+path.name
                add(path,name)
                manifest.append(dict(id=record['id'],pair=record['pair'],label=record['label'],compression=record['compression'],model=model,
                                     image='dataset_sample_v3/'+record['image'],map=name,native_score=native,
                                     sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        assert len(manifest) == 800
        source_records = json.loads((root/'dataset_v3_realistic/metadata.json').read_text(encoding='utf-8'))
        chosen_pairs = {r['pair'] for r in selected}
        archive.writestr('selected_source_annotations.json',json.dumps([r for r in source_records if r['sample_id'] in chosen_pairs],ensure_ascii=False,indent=2))
        archive.writestr('selected_metadata.json',json.dumps(selected,ensure_ascii=False,indent=2))
        archive.writestr('prediction_manifest.json',json.dumps(manifest,indent=2))
        archive.writestr('README.txt','100 paired receipts, 20 pairs per compression; authentic and tampered raw maps for ADCD 512/1024/2048 and TruFor. NPY arrays are original-size forgery probabilities. TruFor NPZ contains map, native score, and confidence. Matching images, official masks, difference masks and metadata are included. SHA256 values refer to the raw prediction files. This bundle is local until explicitly uploaded/shared; paired heatmaps are shared separately on GitHub.')
    temporary.replace(target)
    print('Packaged 100 receipt pairs and 800 raw prediction files:',target)
    return target


if __name__ == '__main__': package()
