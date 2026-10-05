import unittest

from security.policy_engine import evaluate_ipsec_security
from security.recommendations import generate_recommendations
from security.risk import calculate_security_risk


class TestSecurityEngine(unittest.TestCase):

    def test_secure_configuration(self):
        config = {
            "detected": True,
            "ike_version": "IKEv2",
            "encryption": "AES-256-GCM",
            "dh_group": 19,
            "prf": "HMAC-SHA2-384"
        }
        findings = evaluate_ipsec_security(config)
        self.assertEqual(len(findings), 0)
        risk = calculate_security_risk(findings)
        self.assertEqual(risk["score"], 0)
        self.assertEqual(risk["level"], "SECURE")

    def test_insecure_dh_group(self):
        config = {
            "detected": True,
            "ike_version": "IKEv2",
            "encryption": "AES-256-GCM",
            "dh_group": 2, # Forbidden DH Group 2
            "prf": "HMAC-SHA2-256"
        }
        findings = evaluate_ipsec_security(config)
        self.assertGreaterEqual(len(findings), 1)
        finding_ids = [f.finding_id for f in findings]
        self.assertIn("IPSEC-DH-001", finding_ids)

        recs = generate_recommendations(findings)
        self.assertEqual(len(recs), len(findings))

        risk = calculate_security_risk(findings)
        self.assertGreater(risk["score"], 0)
        self.assertIn(risk["level"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_unknown_parameter_not_insecure(self):
        config = {
            "detected": True,
            "ike_version": "IKEv2",
            "encryption": "unknown",
            "pfs": "unknown"
        }
        findings = evaluate_ipsec_security(config)
        self.assertEqual(len(findings), 0) # Unknown params must not generate false findings

if __name__ == "__main__":
    unittest.main()
