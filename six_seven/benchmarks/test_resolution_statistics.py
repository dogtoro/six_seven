import unittest
import pandas as pd
from v3_resolution_report import probability_statistics


class ResolutionStatisticsTests(unittest.TestCase):
    def test_image_max_and_pixel_mean_are_separate_statistics(self):
        frame = pd.DataFrame(dict(prob_max=[.2,.8],prob_mean=[.1,.3],prob_fraction_ge_0_5=[0,.02]))
        result = probability_statistics(frame)
        self.assertAlmostEqual(result['mean_image_max_probability'],.5)
        self.assertAlmostEqual(result['mean_pixel_probability'],.2)
        self.assertAlmostEqual(result['mean_predicted_positive_fraction'],.01)
        self.assertAlmostEqual(result['fraction_images_max_ge_0_5'],.5)

    def test_invalid_probability_cannot_enter_report(self):
        frame = pd.DataFrame(dict(prob_max=[float('nan')],prob_mean=[.1],prob_fraction_ge_0_5=[0]))
        with self.assertRaises(AssertionError): probability_statistics(frame)
