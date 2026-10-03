import unittest

from security.explainability import generate_plain_english_explanations


class TestExplainabilityEngine(unittest.TestCase):

    def test_strong_ikev2_aes_gcm_explanations(self):
        config = {
            "detected": True,
            "ike_version": "IKEv2",
            "encryption": "AES-256-GCM",
            "dh_group": 19,
            "pfs": True,
            "mode": "Tunnel"
        }
        traffic = {
            "status": "success",
            "traffic_type": "CHAT",
            "confidence": 0.477
        }
        explanations = generate_plain_english_explanations(config, traffic)

        self.assertGreaterEqual(len(explanations), 5)
        params = [e["parameter"] for e in explanations]
        self.assertIn("IKE Protocol Version", params)
        self.assertIn("Encryption Cipher Algorithm", params)
        self.assertIn("Diffie-Hellman Key Exchange", params)
        self.assertIn("Perfect Forward Secrecy (PFS)", params)
        self.assertIn("IPsec Encapsulation Mode", params)
        self.assertIn("AI Encrypted Traffic Intelligence", params)

        # Check IKEv2 card details
        ike_card = next(e for e in explanations if e["parameter"] == "IKE Protocol Version")
        self.assertEqual(ike_card["status"], "SECURE")
        self.assertTrue(ike_card["observed_value"].startswith("IKEv2"))
        self.assertIn("IKEv2", ike_card["title"])

        # Check AES-256-GCM card details
        aes_card = next(e for e in explanations if e["parameter"] == "Encryption Cipher Algorithm")
        self.assertEqual(aes_card["status"], "SECURE")
        self.assertIn("AES-256-GCM", aes_card["title"])

    def test_weak_ikev1_3des_dh2_explanations(self):
        config = {
            "detected": True,
            "ike_version": "IKEv1",
            "encryption": "3DES-CBC",
            "dh_group": 2,
            "pfs": False,
            "mode": "Transport"
        }
        explanations = generate_plain_english_explanations(config)

        ike_card = next(e for e in explanations if e["parameter"] == "IKE Protocol Version")
        self.assertEqual(ike_card["status"], "WEAK")

        cipher_card = next(e for e in explanations if e["parameter"] == "Encryption Cipher Algorithm")
        self.assertEqual(cipher_card["status"], "OBSOLETE")

        dh_card = next(e for e in explanations if e["parameter"] == "Diffie-Hellman Key Exchange")
        self.assertEqual(dh_card["status"], "WEAK")

        pfs_card = next(e for e in explanations if e["parameter"] == "Perfect Forward Secrecy (PFS)")
        self.assertEqual(pfs_card["status"], "WEAK")

    def test_edge_case_ciphers_and_groups_explanations(self):
        # Edge Case: Camellia-256 cipher & DH Group 31 (Curve448)
        config = {
            "detected": True,
            "ike_version": "IKEv2",
            "encryption": "CAMELLIA-256",
            "dh_group": "31",
            "pfs": True,
            "mode": "Tunnel"
        }
        explanations = generate_plain_english_explanations(config)

        cipher_card = next(e for e in explanations if e["parameter"] == "Encryption Cipher Algorithm")
        self.assertEqual(cipher_card["status"], "SECURE")
        self.assertIn("Camellia", cipher_card["title"])
        self.assertIn("Camellia", cipher_card["detailed_explanation"])

        dh_card = next(e for e in explanations if e["parameter"] == "Diffie-Hellman Key Exchange")
        self.assertEqual(dh_card["status"], "SECURE")
        self.assertIn("Curve448", dh_card["observed_value"])
        self.assertIn("Curve448", dh_card["title"])


if __name__ == "__main__":
    unittest.main()
