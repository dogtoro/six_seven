import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from models import ExternalMaps
from eval_sota import detection_metrics, image_score, visualization_ids, summarize, pixel_metrics


class DetectionScoreTests(unittest.TestCase):
    def test_native_score_is_independent_of_map_max(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            folder = Path(tmp) / 'trufor'
            folder.mkdir()
            np.savez(folder / 'receipt.png.npz', map=np.ones((2, 3)), score=0.12)
            prob, native = ExternalMaps('trufor', pred_root=tmp).predict('receipt.png')
            self.assertEqual(prob.shape, (2, 3))
            self.assertAlmostEqual(image_score('ext:trufor', prob, native, 'native')[0], 0.12)
            self.assertEqual(image_score('ext:trufor', prob, native, 'max')[0], 1.0)

    def test_native_missing_score_falls_back_as_requested(self):
        self.assertEqual(image_score('ext:trufor', np.ones((2, 2)), None, 'native'), (1.0, 'map_max'))

    def test_visualizations_are_paired_despite_input_order(self):
        data = [{'id': f'receipt_{i:04d}_{kind}__png', 'label': label} for label, kind in [(0, 'authentic'), (1, 'tampered')] for i in range(10)]
        selected = visualization_ids(list(reversed(data)), 4, 4)
        self.assertEqual(len(selected), 8)
        self.assertEqual({x.replace('_authentic__','__') for x in selected if '_authentic__' in x}, {x.replace('_tampered__','__') for x in selected if '_tampered__' in x})

    def test_adcd_falls_back_to_map_score(self):
        self.assertEqual(image_score('ext:adcdnet', np.full((2, 2), 0.3), None, 'native'), (0.3, 'map_max'))

    def test_baseline_detection_is_not_applicable(self):
        for model in ['ela', 'random']:
            score, method = image_score(model, np.ones((2, 2)), None, 'max')
            self.assertTrue(np.isnan(score))
            self.assertEqual(method, 'not_applicable')
        self.assertTrue(all(np.isnan(v) for v in detection_metrics([0, 1], [np.nan, np.nan])))

    def test_native_detection_ranking(self):
        self.assertEqual(detection_metrics([0, 1], [0.1, 0.9])[0], 1.0)

    def test_baseline_summary_suppresses_even_finite_scores(self):
        rows = [dict(model='ela',label=0,score=.1),dict(model='ela',label=1,score=.9,**pixel_metrics(np.ones((2,2)),np.ones((2,2),dtype=bool)))]
        summary = summarize(pd.DataFrame(rows),None)
        self.assertTrue(summary[['det_AUC','det_F1@0.5','det_F1_best']].isna().all().all())


if __name__ == '__main__':
    unittest.main()
