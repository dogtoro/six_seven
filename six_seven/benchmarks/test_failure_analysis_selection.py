import unittest
from collections import Counter
from package_v3_failure_analysis import select_records, VARIANTS


class FailureSelectionTests(unittest.TestCase):
    def test_selection_is_paired_and_spans_compressions(self):
        records = [dict(pair=f'receipt_{i:04d}',compression=v,label=label) for i in range(300) for v in VARIANTS for label in [0,1]]
        selected = select_records(records)
        self.assertEqual(len(selected),200)
        self.assertEqual(len({r['pair'] for r in selected}),100)
        self.assertEqual(Counter(r['compression'] for r in selected),dict.fromkeys(VARIANTS,40))
        for a,t in zip(selected[::2],selected[1::2]):
            self.assertEqual((a['pair'],a['compression']),(t['pair'],t['compression']))
            self.assertEqual((a['label'],t['label']),(0,1))

    def test_insufficient_pairs_fail(self):
        with self.assertRaises(ValueError): select_records([])
