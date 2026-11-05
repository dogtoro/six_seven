import unittest

from eval_sota import require_complete_predictions


class PredictionCompletenessTests(unittest.TestCase):
    def test_rejects_partial_model_predictions(self):
        with self.assertRaisesRegex(RuntimeError, "2/3"):
            require_complete_predictions("ext:trufor", 2, 3)

    def test_accepts_complete_model_predictions(self):
        require_complete_predictions("ext:trufor", 3, 3)


if __name__ == "__main__":
    unittest.main()
