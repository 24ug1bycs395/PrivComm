import unittest

from ml.xgboost_adapter import predict_traffic_class


class TestXGBoostAdapter(unittest.TestCase):

    def test_insufficient_features(self):
        res = predict_traffic_class({})
        self.assertEqual(res["status"], "insufficient_features")

    def test_sample_prediction(self):
        sample_dict = {
            "duration": 143704195.0,
            "total_fiat": 143704195.0,
            "total_biat": 42106019.0,
            "min_fiat": 64.0,
            "min_biat": 20.0,
            "max_fiat": 101572528.0,
            "max_biat": 382847.0,
            "mean_fiat": 101674.9,
            "mean_biat": 53919.1,
            "flowPktsPerSecond": 8.54,
            "flowBytesPerSecond": 1610.0,
            "min_flowiat": 19.0,
            "max_flowiat": 101572528.0,
            "mean_flowiat": 117473.7,
            "std_flowiat": 137463.7,
            "min_active": -1.0,
            "mean_active": 0.0,
            "max_active": -1.0,
            "std_active": 0.0,
            "min_idle": -1.0,
            "mean_idle": 0.0,
            "max_idle": 101572528.0,
            "std_idle": 0.0
        }
        res = predict_traffic_class(sample_dict)
        self.assertEqual(res["status"], "success")
        self.assertIn("traffic_type", res)
        self.assertIn("confidence", res)
        self.assertGreater(res["confidence"], 0.0)

if __name__ == "__main__":
    unittest.main()
