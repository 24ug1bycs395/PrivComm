"""
Optional Google Gemini LLM & Local Knowledge Base Assistant Module for Privcomm.

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


def _invoke_llm(prompt: str, temperature: float = 0.2, max_tokens: int = 300) -> Optional[str]:
    """
    Executes an LLM inference call using either:
    1. EasyCLIProxyAPI / CLIProxyAPI (if LLM_BASE_URL or GEMINI_BASE_URL is set, e.g. http://127.0.0.1:8317/v1)
    2. Direct Google Gemini API (if GEMINI_API_KEY is provided and no local proxy)
    Supports both OpenAI compatible (/v1/chat/completions) and Gemini native (/v1beta/models/...) formats.
    """
    base_url = os.environ.get("LLM_BASE_URL") or os.environ.get("GEMINI_BASE_URL")
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("LLM_MODEL") or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

    # If no custom base_url and no valid GEMINI_API_KEY, return None (triggers local KB fallback)
    if not base_url:
        if not api_key or api_key == "your_gemini_api_key_here":
            return None
        base_url = "https://generativelanguage.googleapis.com"

    base_url = base_url.rstrip("/")
    timeout_sec = float(os.environ.get("LLM_TIMEOUT", "45.0"))

    # Determine whether to use OpenAI format or Gemini format
    # EasyCLIProxyAPI / CLIProxyAPI standard is http://127.0.0.1:8317/v1 or http://127.0.0.1:8317
    is_openai_format = (
        ("/v1" in base_url and "/v1beta" not in base_url)
        or base_url.endswith("/chat/completions")
        or (("localhost" in base_url or "127.0.0.1" in base_url) and "/v1beta" not in base_url)
    )

    try:
        if is_openai_format:
            # OpenAI /v1/chat/completions format
            endpoint = base_url
            if not endpoint.endswith("/chat/completions"):
                if not endpoint.endswith("/v1"):
                    endpoint = f"{endpoint}/v1"
                endpoint = f"{endpoint}/chat/completions"

            headers = {"Content-Type": "application/json"}
            if api_key and api_key != "your_gemini_api_key_here":
                headers["Authorization"] = f"Bearer {api_key}"

            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    choices = res_json.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
        else:
            # Google Gemini format
            if base_url.endswith("/v1beta"):
                endpoint = f"{base_url}/models/{model}:generateContent"
            elif "/models/" not in base_url:
                endpoint = f"{base_url}/v1beta/models/{model}:generateContent"
            else:
                endpoint = base_url

            if api_key and api_key != "your_gemini_api_key_here":
                separator = "&" if "?" in endpoint else "?"
                endpoint = f"{endpoint}{separator}key={api_key}"

            headers = {"Content-Type": "application/json"}
            if api_key and api_key != "your_gemini_api_key_here":
                headers["x-goog-api-key"] = api_key

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()

    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            pass

        # If proxy complained about missing -high suffix (common with Antigravity provider in EasyCLIProxyAPI)
        if "model_not_found" in err_body and not model.endswith("-high"):
            fallback_model = f"{model}-high"
            logger.info(f"[LLM] Model '{model}' not found in proxy, attempting retry with '{fallback_model}'...")
            try:
                os.environ["LLM_MODEL"] = fallback_model
                return _invoke_llm(prompt, temperature=temperature, max_tokens=max_tokens)
            except Exception:
                pass

        logger.warning(f"[LLM] HTTP {e.code} error from LLM endpoint ({base_url}): {err_body or e}")
    except Exception as e:
        logger.warning(f"[LLM] Connection error to LLM endpoint ({base_url}): {e}")

    return None


def query_gemini_explainer(parameter_name: str, observed_value: str) -> Optional[Dict[str, Any]]:
    """
    Query LLM API (Gemini or EasyCLIProxyAPI proxy) to generate a plain-English explanation card
    for an edge-case IPsec parameter.
    """
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

    text_out = _invoke_llm(prompt, temperature=0.2, max_tokens=250)
    if text_out:
        try:
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
                "icon": "",
                "title": f" AI: {card_data.get('title', parameter_name)}",
                "plain_english_summary": card_data.get("plain_english_summary", ""),
                "detailed_explanation": card_data.get("detailed_explanation", "")
            }
        except Exception as e:
            logger.debug(f"Could not parse LLM explanation card JSON: {e}")

    return None


def query_gemini_assistant(user_message: str) -> str:
    """
    Interactive Assistant endpoint used by the Web UI Chatbot widget.
    Queries LLM (Gemini or EasyCLIProxyAPI proxy) if configured; otherwise returns local cybersecurity KB responses.
    """
    prompt = (
        "You are Privcomm AI, an elite cybersecurity and IPsec VPN security intelligence assistant.\n"
        "Format your response to be visually stunning, structured, and effortless to read in a modern chat UI.\n\n"
        "FORMATTING & STYLE RULES:\n"
        "1. EXECUTIVE SUMMARY: Start with 1 crisp sentence explaining the core concept directly.\n"
        "2. SECTION HEADINGS: Group your answer into clean sections using bold titles with relevant emojis (e.g. 🛡️ **Security Mechanics**, ⚙️ **Key Components**, 📜 **RFC Standards**, ⚠️ **Compliance Impact**, 💡 **Remediation Action**).\n"
        "3. SCANNABLE BULLET POINTS: Use short, concise bullet points (•). Bold the first 2-3 words of each bullet point (e.g., '• **Parameter Matching:** Compares active SAs...'). Avoid large walls of text.\n"
        "4. TECHNICAL TERMS: Highlight all cipher names, RFCs, protocols, and ports with inline code backticks (e.g. `AES-256-GCM`, `RFC 7296`, `DH Group 19`, `PCI-DSS 4.0`).\n"
        "5. SIMPLIFICATIONS / '5 YR OLD': If the user asks for a simple, intuitive, or child-friendly explanation, use vivid, fun everyday analogies (e.g., secret codes, armored tunnels) with zero confusing jargon.\n"
        "6. BREVITY: Keep the total response under 4-5 focused bullet points or 2 short sections.\n\n"
        f"User Question: {user_message}"
    )

    text_out = _invoke_llm(prompt, temperature=0.3, max_tokens=1024)
    if text_out:
        return text_out

    # Fallback: Zero-latency Local Cybersecurity Knowledge Base Engine
    msg_lower = user_message.lower()

    if "dh" in msg_lower or "diffie" in msg_lower or "group 19" in msg_lower or "group 2" in msg_lower:
        return (
            " **Diffie-Hellman (DH) Key Exchange Explanation:**\n"
            "• **DH Group 19 (ECP-256):** Recommended bank-grade Elliptic Curve key exchange. Allows VPN endpoints to agree on encryption keys securely with fast execution.\n"
            "• **DH Group 14 (MODP-2048):** Standard corporate baseline using 2048-bit prime numbers.\n"
            "• **DH Group 2 (MODP-1024):**  Deprecated & Weak! 1024-bit prime keys can be precomputed by GPU clusters (Logjam vulnerability)."
        )

    if "3des" in msg_lower or "des" in msg_lower or "cipher" in msg_lower or "aes" in msg_lower or "gcm" in msg_lower:
        return (
            " **Encryption Cipher Baselines:**\n"
            "• **AES-256-GCM:** High-speed AEAD encryption that scrambles data and verifies message integrity in a single pass (Tamper-Proof).\n"
            "• **AES-256-CBC:** Strong block cipher, requiring a separate HMAC hash check.\n"
            "• **3DES / DES:**  Obsolete 1990s ciphers! Vulnerable to Sweet32 birthday attacks where eavesdroppers recover cleartext data."
        )

    if "ikev1" in msg_lower or "ikev2" in msg_lower or "version" in msg_lower or "protocol" in msg_lower:
        return (
            " **IKE Protocol Negotiation:**\n"
            "• **IKEv2 (Modern):** Fast, resilient, supports MOBIKE (seamless roaming between Wi-Fi and 5G/4G), auto-heals dropped tunnels.\n"
            "• **IKEv1 (Legacy):** Slower negotiation requiring extra network round-trips; aggressive mode exposes pre-shared key hashes to offline dictionary attacks."
        )

    if "pfs" in msg_lower or "forward secrecy" in msg_lower:
        return (
            " **Perfect Forward Secrecy (PFS):**\n"
            "PFS generates a fresh, independent temporary key for every single session. "
            "Even if an attacker steals your master VPN server key five years in the future, they cannot retroactively decrypt any past recorded traffic!"
        )

    if "ai" in msg_lower or "xgboost" in msg_lower or "traffic" in msg_lower or "classify" in msg_lower:
        return (
            " **AI Encrypted Traffic Classification:**\n"
            "Our XGBoost machine learning model extracts 28 statistical flow features (packet size distributions, inter-arrival timing, burstiness) "
            "to identify application activity (e.g., CHAT, VOIP, STREAMING, P2P, MALWARE) with statistical confidence, without needing to decrypt the payload!"
        )

    if "upgrade" in msg_lower or "fix" in msg_lower or "remediat" in msg_lower or "cisco" in msg_lower or "strongswan" in msg_lower:
        return (
            " **Remediation & Compliance Action Plan:**\n"
            "1. Change IKE phase 1 protocol from `IKEv1` to `IKEv2`.\n"
            "2. Update phase 1 & 2 proposals to `AES-256-GCM` or `AES-256-CBC` with `HMAC-SHA2-256`.\n"
            "3. Replace DH Group 2/5 with `DH Group 19 (ECP-256)` or `DH Group 14 (MODP-2048)`.\n"
            "4. Ensure `PFS (Perfect Forward Secrecy)` is set to Enforced."
        )

    return (
        " **Privcomm Security Assistant**\n"
        "I am ready to help you analyze your IPsec VPN security posture, cryptographic parameters, risk scores, or traffic classifications!\n\n"
        "You can ask me questions like:\n"
        "• *'Why is DH Group 2 considered weak?'*\n"
        "• *'What is the difference between AES-GCM and AES-CBC?'*\n"
        "• *'How does AI classify traffic without decryption?'*\n"
        "• *'How do I upgrade my VPN configuration?'*"
    )
