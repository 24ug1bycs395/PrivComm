"""
Unit tests for Enterprise Auditing Modules:
- Configuration Drift Detector
- Policy-as-Code Rulebook Evaluator
- Post-Quantum Readiness Assessor
"""

import unittest
from security.drift_detector import detect_configuration_drift
from security.policy_engine import evaluate_policy_as_code_rules
from security.pqc_assessor import evaluate_post_quantum_readiness


class TestEnterpriseAuditing(unittest.TestCase):

    def setUp(self):
        self.strong_config = {
            "ike_version": "IKEv2",
            "encryption": "AES-256-GCM",
            "dh_group": "19",
            "pfs": True,
            "mode": "Tunnel",
            "integrity": "AEAD"
        }

        self.weak_config = {
            "ike_version": "IKEv1 (Aggressive Mode)",
            "encryption": "3DES-CBC",
            "dh_group": "2",
            "pfs": False,
            "mode": "Transport",
            "integrity": "MD5"
        }

    def test_drift_detector_synchronized(self):
        res = detect_configuration_drift(self.strong_config)
        self.assertFalse(res["drift_detected"])
        self.assertEqual(res["drift_status"], "SYNCHRONIZED")
        self.assertEqual(res["variance_score"], 0)

    def test_drift_detector_drifted(self):
        res = detect_configuration_drift(self.weak_config)
        self.assertTrue(res["drift_detected"])
        self.assertEqual(res["drift_status"], "DRIFTED")
        self.assertGreater(res["variance_score"], 50)

    def test_policy_as_code_pass(self):
        res = evaluate_policy_as_code_rules(self.strong_config)
        self.assertEqual(res["compliance_score"], 100)
        self.assertEqual(res["failed"], 0)

    def test_policy_as_code_fail(self):
        res = evaluate_policy_as_code_rules(self.weak_config)
        self.assertLess(res["compliance_score"], 50)
        self.assertGreater(res["failed"], 0)

    def test_pqc_assessor_transitional(self):
        res = evaluate_post_quantum_readiness(self.strong_config)
        self.assertIn("PQC", res["pqc_status"])
        self.assertIn("pqc_checks", res)

    def test_pqc_assessor_vulnerable(self):
        res = evaluate_post_quantum_readiness(self.weak_config)
        self.assertEqual(res["pqc_status"], "CLASSICAL_VULNERABLE")
        self.assertEqual(res["quantum_threat_rating"], "HIGH_RISK_SNDL")


if __name__ == "__main__":
    unittest.main()
