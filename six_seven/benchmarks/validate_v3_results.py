"""Verify standalone V3 output coverage and scoring."""
from pathlib import Path
import json
import pandas as pd
from package_v3_failure_analysis import package
from publish_v3 import publish

root = Path(__file__).resolve().parent
records = json.loads((root.parent / 'dataset_sample_v3/metadata.json').read_text(encoding='utf-8'))
ids = {r['id'] for r in records}
assert len(records) == len(ids) == 3000
for kind in ['official_mask','diff_mask']:
    folder = root / 'results_v3_realistic' / kind
    frame = pd.read_csv(folder / 'per_image.csv')
    assert len(frame) == 18000
    assert set(frame.model) == {'ext:trufor','ext:adcdnet','ext:adcdnet_1024','ext:adcdnet_2048','ela','random'}
    for model, group in frame.groupby('model'):
        assert len(group) == 3000 and group.id.is_unique and set(group.id) == ids
        assert group.groupby('label').size().to_dict() == {0:1500,1:1500}
        assert group.loc[group.label == 1,'f1@0.5'].notna().all()
        assert group[['prob_max','prob_mean','prob_fraction_ge_0_5']].notna().all().all()
    assert frame.loc[frame.model == 'ext:trufor','score_source'].eq('native').all()
    summary = pd.read_csv(folder / 'summary.csv')
    assert summary.loc[summary.model.isin(['ela','random']),['det_AUC','det_F1@0.5','det_F1_best']].isna().all().all()
    for model in ['ext_trufor','ext_adcdnet','ext_adcdnet_1024','ext_adcdnet_2048','ela','random']:
        views = list((folder / 'vis' / model).glob('*.png'))
        a = {p.stem.replace('_authentic__','__') for p in views if '_authentic__' in p.stem}
        t = {p.stem.replace('_tampered__','__') for p in views if '_tampered__' in p.stem}
        assert len(a & t) >= 200
(root.parent / 'feedback_stage.txt').write_text('V3: package raw probability maps for 100 paired receipts')
bundle = package()
(root.parent / 'feedback_stage.txt').write_text('V3: publish verified reports and paired heatmaps to dam')
publication = publish()
(root.parent / 'v3_complete.json').write_text(json.dumps(dict(status='Complete, verified and published',images=3000,models=6,rows_per_ground_truth=18000,adcd_max_sizes=[512,1024,2048],raw_map_bundle=str(bundle),publication=publication),indent=2))
print('PASS: standalone V3 coverage, native scores, baseline N/A detection, paired views')
