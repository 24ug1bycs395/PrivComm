import os
import unittest

from analyzer.ipsec_parser import synthesize_ipsec_config
from analyzer.pcap_ingestion import ingest_and_parse_pcap


class TestIPsecParser(unittest.TestCase):

    def test_synthesize_config_unobservable(self):
        ike_info = {"ike_detected": False}
        esp_info = {"esp_detected": False}
        res = synthesize_ipsec_config(ike_info, esp_info)
        self.assertFalse(res["detected"])
        self.assertEqual(res["encryption"], "unknown")
        self.assertEqual(res["dh_group"], "unknown")

    def test_sample_pcap_parsing(self):
        sample_path = "samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng"
        if not os.path.exists(sample_path):
            self.skipTest("Sample PCAP not found")

        res = ingest_and_parse_pcap(sample_path)
        self.assertEqual(res["status"], "success")
        ipsec = res["ipsec"]
        self.assertTrue(ipsec["detected"])
        self.assertTrue(ipsec["ike_detected"])
        self.assertEqual(ipsec["ike_version"], "IKEv2")
        self.assertEqual(ipsec["encryption"], "AES-256-GCM")
        self.assertEqual(ipsec["dh_group"], 19)

if __name__ == "__main__":
    unittest.main()
