/**
 * Pollinations AI Integration for Privcomm Cyber Sentinel Assistant
 * Uses Pollinations.ai API to provide AI-powered IPsec & Cybersecurity analysis.
 */

const POLLINATIONS_API_KEY = import.meta.env.VITE_POLLINATIONS_API_KEY || '';

const SYSTEM_PROMPT = `You are Cyber Sentinel, an expert AI Security Intelligence Assistant embedded in Privcomm — the AI-Assisted IPsec VPN Security Intelligence & Traffic Classification Platform.

Your expertise includes:
- IPsec Protocols: IKEv1, IKEv2 (RFC 7296), ESP (RFC 4303), AH (RFC 4302), NAT-Traversal (UDP 4500), ISAKMP (UDP 500).
- Cryptographic Suites: AES-GCM (128/256), ChaCha20-Poly1305, AES-CBC, 3DES (deprecated), DES (vulnerable), SHA-2/3, HMAC-MD5 (broken), HMAC-SHA1 (weak).
- Key Exchange / PFS: Diffie-Hellman Groups (Group 1, 2, 5 = weak; Group 14, 19, 20, 21 = strong/recommended), Post-Quantum Hybrids (Kyber/ML-KEM).
- Compliance Standards: NIST SP 800-77 Rev 1, FIPS 140-3, NSA CSfC (Commercial Solutions for Classified), ANSSI, RFC 8221 cryptographic suites.
- Traffic Classification: Machine learning flow analysis, XGBoost classification, packet entropy, burstiness, timing metadata, anomaly detection.

Formatting guidelines:
- Keep answers clear, professional, concise, and technically accurate.
- Use markdown formatting (**bold** for key concepts, \`code\` for algorithms/ports/ciphers, bullet points for lists).
- If explaining vulnerabilities, give specific remediation steps.`;

/**
 * Ask Pollinations AI a question with optional context
 * @param {string} userPrompt - The user's input message
 * @param {object} [context] - Current inspection telemetry / risk data
 * @returns {Promise<string>} - The AI generated response
 */
export async function askCyberSentinel(userPrompt, context = null) {
  let fullPrompt = userPrompt;

  if (context && typeof context === 'object') {
    const contextSummary = `
[Observed Session Telemetry Context]
- IKE Version: ${context.ike_version || 'N/A'}
- Mode: ${context.mode || 'N/A'}
- Encryption: ${context.encryption || 'N/A'}
- Integrity: ${context.integrity || 'N/A'}
- DH Group: ${context.dh_group || 'N/A'} (PFS: ${context.pfs ? 'Enabled' : 'Disabled'})
- Computed Risk Score: ${context.security_assessment?.risk_score ?? 'N/A'}/100 (${context.security_assessment?.risk_level || 'N/A'})
- Traffic Class: ${context.traffic_classification?.traffic_type || 'N/A'}
`;
    fullPrompt = `${contextSummary}\nUser Question: ${userPrompt}`;
  }

  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: fullPrompt }
  ];

  try {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (POLLINATIONS_API_KEY) {
      headers['Authorization'] = `Bearer ${POLLINATIONS_API_KEY}`;
    }

    const response = await fetch('https://text.pollinations.ai/openai', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        messages,
        model: 'openai',
        seed: 42,
        temperature: 0.7,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      const content = data.choices?.[0]?.message?.content;
      if (content) {
        return content.trim();
      }
    }

    // Fallback directly to text endpoint if JSON POST fails
    const encodedPrompt = encodeURIComponent(`${SYSTEM_PROMPT}\n\nUser: ${fullPrompt}`);
    const textUrl = POLLINATIONS_API_KEY
      ? `https://text.pollinations.ai/${encodedPrompt}?key=${encodeURIComponent(POLLINATIONS_API_KEY)}`
      : `https://text.pollinations.ai/${encodedPrompt}`;

    const textRes = await fetch(textUrl);
    if (textRes.ok) {
      const textOutput = await textRes.text();
      if (textOutput && textOutput.trim().length > 0) {
        return textOutput.trim();
      }
    }
  } catch (err) {
    console.warn('Pollinations AI request error:', err);
  }

  // Fallback domain response if offline
  return getLocalFallbackResponse(userPrompt);
}

/**
 * Intelligent local fallback when network or API is unavailable
 */
function getLocalFallbackResponse(prompt) {
  const p = prompt.toLowerCase();

  if (p.includes('3des') || p.includes('des') || p.includes('dh group 2') || p.includes('weak')) {
    return `### **Cryptographic Weakness Analysis**\n\n* **3DES (Triple-DES)**: Vulnerable to the Sweet32 attack (64-bit block size collision). Deprecated by NIST SP 800-77 since 2023.\n* **DH Group 2 (1024-bit)**: Broken by state-level adversaries utilizing Number Field Sieve precomputations (Logjam attack).\n* **Remediation**: Upgrade to **AES-256-GCM** (AEAD) and **DH Group 19 (ECDH Curve P-256)** or **Group 21 (Curve P-521)**.`;
  }

  if (p.includes('stream') || p.includes('live') || p.includes('rationale')) {
    return `### **Live Stream Ingestion Rationale**\n\n* **Zero-Exfiltration Inspection**: Packets are parsed strictly in-memory using packet dissector buffers without persisting unencrypted plaintext.\n* **Statistical ML Classification**: XGBoost derives 28 flow features (entropy, burst timing, packet length variance) to detect tunneled application signatures through active ESP encapsulation.`;
  }

  if (p.includes('remediation') || p.includes('risk') || p.includes('high risk')) {
    return `### **High-Risk IPsec Tunnel Remediation**\n\n1. **Migrate to IKEv2**: Eliminate IKEv1 Aggressive Mode Pre-Shared Key exposure.\n2. **Enforce AEAD**: Replace CBC-mode ciphers with \`AES-256-GCM\` or \`ChaCha20-Poly1305\` to mitigate padding oracle vulnerabilities.\n3. **Mandate PFS (Perfect Forward Secrecy)**: Enforce ephemeral key exchanges with Diffie-Hellman Group >= 14.\n4. **Post-Quantum Strategy**: Prepare transition to hybrid ML-KEM/Kyber Key Exchange.`;
  }

  return `### **Cyber Sentinel Advisory**\n\nI have analyzed your query regarding **"${prompt}"**.\n\n* **Protocol Compliance**: NIST SP 800-77 Rev 1 mandates using IKEv2 with AES-GCM and PFS enabled.\n* **Integrity & Secrecy**: Ensure ESP is configured with AEAD algorithms for authenticated encryption.\n* If you need detailed remediation for a specific capture file, click on any metric card in the Telemetry Dashboard.`;
}
