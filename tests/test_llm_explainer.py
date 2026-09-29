import unittest
import os
from unittest.mock import patch, MagicMock
from security.llm_explainer import _invoke_llm, query_gemini_assistant, query_gemini_explainer


class TestLLMExplainerProxy(unittest.TestCase):

    def test_fallback_when_unconfigured(self):
        with patch.dict(os.environ, {"LLM_BASE_URL": "", "GEMINI_API_KEY": ""}, clear=True):
            resp = query_gemini_assistant("What is DH Group 19?")
            self.assertIn("Diffie-Hellman", resp)

    @patch("urllib.request.urlopen")
    def test_openai_format_proxy_call(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"choices": [{"message": {"content": "Test proxy AI response"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with patch.dict(os.environ, {
            "LLM_BASE_URL": "http://127.0.0.1:8317/v1",
            "LLM_API_KEY": "sk-test",
            "LLM_MODEL": "gemini-2.5-flash"
        }, clear=True):
            resp = query_gemini_assistant("Hello assistant")
            self.assertEqual(resp, "Test proxy AI response")

    @patch("urllib.request.urlopen")
    def test_explainer_card_proxy_call(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"choices": [{"message": {"content": "{\\"title\\": \\"AES Encryption\\", \\"plain_english_summary\\": \\"Secures traffic\\", \\"detailed_explanation\\": \\"Provides confidentiality\\", \\"status\\": \\"SECURE\\"}"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with patch.dict(os.environ, {
            "LLM_BASE_URL": "http://127.0.0.1:8317/v1",
            "LLM_API_KEY": "sk-test",
            "LLM_MODEL": "gemini-2.5-flash"
        }, clear=True):
            card = query_gemini_explainer("Encryption Cipher Algorithm", "AES-256-GCM")
            self.assertIsNotNone(card)
            self.assertEqual(card["status"], "SECURE")
            self.assertIn("AES Encryption", card["title"])


if __name__ == "__main__":
    unittest.main()
