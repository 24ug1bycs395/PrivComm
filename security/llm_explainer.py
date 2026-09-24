"""
Optional Google Gemini LLM & Local Knowledge Base Assistant Module for Cyber Sentinel.

Provides dynamic AI assistant responses for the Web UI Chatbot widget.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger("LLMExplainer")


def load_env_file():
    """Simple zero-dependency .env file parser."""
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception as e:
            logger.warning(f"Could not parse .env file: {e}")


# Automatically load .env on module import
load_env_file()


def query_gemini_explainer(parameter_name: str, observed_value: str) -> Optional[Dict[str, Any]]:
    """
    Query Google Gemini LLM API to generate a plain-English explanation card
    for an edge-case IPsec parameter.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None

    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    prompt = (
        f"You are a cybersecurity expert explaining IPsec VPN configuration parameters to non-technical business executives.\n"
        f"Target Parameter: '{parameter_name}'\n"
        f"Observed Technical Value: '{observed_value}'\n\n"
        f"Respond STRICTLY in valid JSON format with no markdown fences:\n"
        f"{{\n"
        f'  "title": "Short Non-Technical Concept Name",\n'
        f'  "plain_english_summary": "One sentence non-expert summary of what this component does",\n'
        f'  "detailed_explanation": "Two sentences explaining its security significance and why it matters in plain English",\n'
        f'  "status": "SECURE or WEAK or OBSOLETE or INFO"\n'
        f"}}\n"
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 200
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                resp_bytes = resp.read()
                res_json = json.loads(resp_bytes.decode("utf-8"))
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text_out = parts[0].get("text", "").strip()
                        if text_out.startswith("```json"):
                            text_out = text_out[7:]
                        if text_out.startswith("```"):
                            text_out = text_out[3:]
                        if text_out.endswith("```"):
                            text_out = text_out[:-3]
                        text_out = text_out.strip()

                        card_data = json.loads(text_out)
                        return {
                            "parameter": parameter_name,
                            "observed_value": observed_value,
                            "status": card_data.get("status", "INFO"),
                            "icon": "🧠",
                            "title": f"✨ AI (Gemini): {card_data.get('title', parameter_name)}",
                            "plain_english_summary": card_data.get("plain_english_summary", ""),
                            "detailed_explanation": card_data.get("detailed_explanation", "")
                        }
    except Exception as e:
        logger.debug(f"Gemini LLM explainability query skipped/fallback: {e}")

    return None


def query_gemini_assistant(user_message: str) -> str:
    """
    Interactive Assistant endpoint used by the Web UI Chatbot widget.
    Queries Gemini LLM API if key is present; otherwise returns local cybersecurity KB responses.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        prompt = (
            "You are Cyber Sentinel AI, an expert cybersecurity assistant for IPsec VPN analysis and encrypted traffic intelligence. "
            "Help non-technical business leaders and security teams understand IPsec protocols, AES ciphers, DH Groups, PFS, "
            "risk scores, and remediation steps in clear, professional, and intuitive terms. Keep responses concise (2-4 bullet points or short paragraphs).\n\n"
            f"User Question: {user_message}"
        )

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 300
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    resp_bytes = resp.read()
                    res_json = json.loads(resp_bytes.decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
        except Exception as e:
            logger.debug(f"Gemini API assistant call skipped/failed: {e}")

    # Fallback: Zero-latency Local Cybersecurity Knowledge Base Engine
    msg_lower = user_message.lower()

    if "dh" in msg_lower or "diffie" in msg_lower or "group 19" in msg_lower or "group 2" in msg_lower:
        return (
            "🤝 **Diffie-Hellman (DH) Key Exchange Explanation:**\n"
            "• **DH Group 19 (ECP-256):** Recommended bank-grade Elliptic Curve key exchange. Allows VPN endpoints to agree on encryption keys securely with fast execution.\n"
            "• **DH Group 14 (MODP-2048):** Standard corporate baseline using 2048-bit prime numbers.\n"
            "• **DH Group 2 (MODP-1024):** ⚠️ Deprecated & Weak! 1024-bit prime keys can be precomputed by GPU clusters (Logjam vulnerability)."
        )

    if "3des" in msg_lower or "des" in msg_lower or "cipher" in msg_lower or "aes" in msg_lower or "gcm" in msg_lower:
        return (
            "🔒 **Encryption Cipher Baselines:**\n"
            "• **AES-256-GCM:** High-speed AEAD encryption that scrambles data and verifies message integrity in a single pass (Tamper-Proof).\n"
            "• **AES-256-CBC:** Strong block cipher, requiring a separate HMAC hash check.\n"
            "• **3DES / DES:** ⚠️ Obsolete 1990s ciphers! Vulnerable to Sweet32 birthday attacks where eavesdroppers recover cleartext data."
        )

    if "ikev1" in msg_lower or "ikev2" in msg_lower or "version" in msg_lower or "protocol" in msg_lower:
        return (
            "📞 **IKE Protocol Negotiation:**\n"
            "• **IKEv2 (Modern):** Fast, resilient, supports MOBIKE (seamless roaming between Wi-Fi and 5G/4G), auto-heals dropped tunnels.\n"
            "• **IKEv1 (Legacy):** Slower negotiation requiring extra network round-trips; aggressive mode exposes pre-shared key hashes to offline dictionary attacks."
        )

    if "pfs" in msg_lower or "forward secrecy" in msg_lower:
        return (
            "🔑 **Perfect Forward Secrecy (PFS):**\n"
            "PFS generates a fresh, independent temporary key for every single session. "
            "Even if an attacker steals your master VPN server key five years in the future, they cannot retroactively decrypt any past recorded traffic!"
        )

    if "ai" in msg_lower or "xgboost" in msg_lower or "traffic" in msg_lower or "classify" in msg_lower:
        return (
            "🧠 **AI Encrypted Traffic Classification:**\n"
            "Our XGBoost machine learning model extracts 28 statistical flow features (packet size distributions, inter-arrival timing, burstiness) "
            "to identify application activity (e.g., CHAT, VOIP, STREAMING, P2P, MALWARE) with statistical confidence, without needing to decrypt the payload!"
        )

    if "upgrade" in msg_lower or "fix" in msg_lower or "remediat" in msg_lower or "cisco" in msg_lower or "strongswan" in msg_lower:
        return (
            "🛡️ **Remediation & Compliance Action Plan:**\n"
            "1. Change IKE phase 1 protocol from `IKEv1` to `IKEv2`.\n"
            "2. Update phase 1 & 2 proposals to `AES-256-GCM` or `AES-256-CBC` with `HMAC-SHA2-256`.\n"
            "3. Replace DH Group 2/5 with `DH Group 19 (ECP-256)` or `DH Group 14 (MODP-2048)`.\n"
            "4. Ensure `PFS (Perfect Forward Secrecy)` is set to Enforced."
        )

    return (
        "🤖 **Cyber Sentinel Security Assistant**\n"
        "I am ready to help you analyze your IPsec VPN security posture, cryptographic parameters, risk scores, or traffic classifications!\n\n"
        "You can ask me questions like:\n"
        "• *'Why is DH Group 2 considered weak?'*\n"
        "• *'What is the difference between AES-GCM and AES-CBC?'*\n"
        "• *'How does AI classify traffic without decryption?'*\n"
        "• *'How do I upgrade my VPN configuration?'*"
    )
