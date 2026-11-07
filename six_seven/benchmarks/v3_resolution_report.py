"""Compare probabilities and localization at 512/1024/2048 on identical V3 inputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from eval_sota import detection_metrics


def probability_statistics(frame):
    values = frame[['prob_max','prob_mean','prob_fraction_ge_0_5']].to_numpy()
    assert np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all()
    return dict(mean_image_max_probability=frame.prob_max.mean(),
                mean_pixel_probability=frame.prob_mean.mean(),
                mean_predicted_positive_fraction=frame.prob_fraction_ge_0_5.mean(),
                fraction_images_max_ge_0_5=(frame.prob_max >= .5).mean())


def main():
    root = Path(__file__).resolve().parent
    records = json.loads((root.parent / 'dataset_sample_v3/metadata.json').read_text(encoding='utf-8'))
    sizes = {r['id']:max(r['size']) for r in records}
    assert len(sizes) == 3000
    rows = []
    for mask in ['official_mask','diff_mask']:
        frame = pd.read_csv(root / 'results_v3_realistic' / mask / 'per_image.csv')
        for cap in [512,1024,2048]:
            model = 'ext:adcdnet' if cap == 512 else f'ext:adcdnet_{cap}'
            data = frame[frame.model == model]
            assert len(data) == 3000 and data.id.is_unique and set(data.id) == set(sizes)
            for label in ['all',0,1]:
                group = data if label == 'all' else data[data.label == label]
                row = dict(mask=mask,max_size=cap,label=label,n=len(group),
                           images_downscaled=sum(sizes[sid] > cap for sid in group.id),
                           pixel_F1_at_0_5=group.loc[group.label == 1,'f1@0.5'].mean(),
                           pixel_IoU_at_0_5=group.loc[group.label == 1,'iou@0.5'].mean(),
                           det_AUC=detection_metrics(group.label,group.score)[0],
                           **probability_statistics(group))
                rows.append(row)
    table = pd.DataFrame(rows)
    out = root / 'results_v3_realistic'
    table.to_csv(out / 'resolution_comparison.csv',index=False)
    overall = table[(table['mask'] == 'official_mask') & (table.label == 'all')]
    report = '# V3 resolution ablation\n\n'
    report += overall.round(6).to_markdown(index=False)
    report += '''\n\nThe earlier approximately 0.44 statistic is the mean of each image's maximum probability. Mean pixel probability and predicted-positive fraction are reported separately. All caps use the same 3,000 V3 image IDs, weights, OCR masks, inference precision and evaluation thresholds. max-size is a downscaling cap; it does not upscale inputs. images_downscaled identifies how many inputs each cap affects.\n\nA probability increase alone does not establish better localization: compare pixel F1/IoU and detection AUC alongside the probabilities. These results quantify resolution sensitivity on V3; they do not prove a single cause of the original V2 behavior or establish calibration on an independent validation set. Class-specific rows are in the CSV.\n'''
    (out / 'RESOLUTION_REPORT.md').write_text(report)
    print('V3 resolution comparison written')


if __name__ == '__main__':
    main()
