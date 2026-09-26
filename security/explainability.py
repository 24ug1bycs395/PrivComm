"""
Component-by-Component Plain-English Security Rationale Engine for IPsec VPN.

Translates specific technical parameters (IKE version, AES ciphers, DH Groups, PFS, Tunnel Mode, AI Classification)
into clear, intuitive, plain-English explanations designed for non-technical stakeholders, auditors, and IT managers.
Includes exact algorithm-specific explanations for AES-256-GCM, AES-128-GCM, AES-256-CBC, 3DES, DH Group 19, Group 14, Group 2, etc.
"""

from typing import Dict, Any, List
from security.llm_explainer import query_gemini_explainer


def generate_plain_english_explanations(
    ipsec_info: Dict[str, Any],
    traffic_res: Dict[str, Any] = None,
    metadata_exposure: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Generates a list of plain-English rationale cards for each technical component
    observed in the IPsec configuration, AI traffic classification, and metadata exposure assessment.
    """
    explanations = []

    # 1. IKE Protocol & Version (Hyper-Specific)
    ike_version = str(ipsec_info.get("ike_version", "")).upper()
    exchange_type = str(ipsec_info.get("exchange_type", "")).upper()

    if "AGGRESSIVE" in ike_version or "AGGRESSIVE" in exchange_type:
        explanations.append({
            "parameter": "IKE Protocol Version",
            "observed_value": "IKEv1 (Aggressive Mode)",
            "status": "WEAK",
            "icon": "",
            "title": "Legacy IKEv1 Aggressive Mode (Vulnerable to Offline Password Cracking)",
            "plain_english_summary": "Outdated 1990s negotiation protocol that broadcasts your VPN authentication password hash over the open internet in plain sight.",
            "detailed_explanation": (
                "IKEv1 Aggressive Mode squeezes the initial connection handshake down to 3 messages to set up tunnels quickly, but it pays a dangerous price: "
                "it broadcasts your pre-shared key (PSK) hash over the public internet without encryption. "
                "Think of it like shouting a secret password across a crowded room. Any hacker or eavesdropper listening on the network can record these 3 messages "
                "and run automated GPU cracking software in the background to discover your organization's master VPN password."
            )
        })
    elif "V2" in ike_version or ike_version == "IKEV2":
        explanations.append({
            "parameter": "IKE Protocol Version",
            "observed_value": "IKEv2 (RFC 7296)",
            "status": "SECURE",
            "icon": "",
            "title": "Modern IKEv2 Protocol Engine (RFC 7296)",
            "plain_english_summary": "Manages your VPN connection lifecycle with high speed, instant auto-reconnect, and seamless network mobility across Wi-Fi and 5G.",
            "detailed_explanation": (
                "IKEv2 acts as the intelligent digital negotiator for your VPN. Imagine traveling on a train where your laptop switches between station Wi-Fi and 5G cellular—older VPNs would freeze or crash, forcing you to log in again. "
                "IKEv2 natively uses MOBIKE (RFC 4555) technology to instantly shift your encrypted session between network connections without dropping active video calls or web apps. "
                "Additionally, it uses a streamlined 4-message exchange (IKE_SA_INIT & IKE_AUTH) with built-in cookie challenges to protect your server against hacker overload (DoS SYN-flood) attacks."
            )
        })
    elif "V1" in ike_version or ike_version == "IKEV1":
        explanations.append({
            "parameter": "IKE Protocol Version",
            "observed_value": "IKEv1 (Main Mode)",
            "status": "WEAK",
            "icon": "",
            "title": "Legacy IKEv1 Main Mode (RFC 2409)",
            "plain_english_summary": "1990s negotiation protocol requiring 6 network round-trips with slow setup times and frequent connection drops.",
            "detailed_explanation": (
                "IKEv1 Main Mode was designed back in 1998. It requires 6 back-and-forth network round-trips just to establish a connection, making setup noticeably slow on mobile networks. "
                "Because it lacks modern mobility support, your VPN will disconnect whenever your computer changes IP addresses or switches Wi-Fi networks. "
                "It is also vulnerable to Denial-of-Service state-exhaustion attacks compared to modern IKEv2."
            )
        })
    else:
        explanations.append({
            "parameter": "IKE Protocol Version",
            "observed_value": ike_version if ike_version and ike_version != "UNKNOWN" else "IKE / IPsec",
            "status": "INFO",
            "icon": "",
            "title": f"Tunnel Negotiation Protocol ({ike_version or 'IKE'})",
            "plain_english_summary": "Manages initial identity verification and security negotiations between your device and the VPN server.",
            "detailed_explanation": (
                "Sets up the initial secure channel between your computer and the remote organizational gateway before sensitive data starts flowing."
            )
        })

    # 2. Encryption Cipher Algorithm & Real-World Edge Cases (Hyper-Specific)
    enc = str(ipsec_info.get("encryption", "")).upper()
    key_len = str(ipsec_info.get("key_length", "256"))

    if "3DES" in enc or "DES" in enc:
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": "3DES-CBC (Triple-DES)",
            "status": "OBSOLETE",
            "icon": "",
            "title": "Obsolete 3DES-CBC Cipher (Vulnerable to Sweet32 Collision Attacks)",
            "plain_english_summary": "Obsolete 1990s 64-bit encryption block cipher that modern high-speed computers can break through data collision attacks.",
            "detailed_explanation": (
                "Triple-DES scrambles data by running the 1970s DES algorithm 3 times in sequence. "
                "However, because it uses tiny 64-bit blocks of data, modern security research (Sweet32 attack / CVE-2016-2183) proves that an eavesdropper capturing around 32GB of high-speed VPN traffic "
                "can mathematically break the encryption and recover secret plaintext data. Formally retired and forbidden by NIST SP 800-131A guidelines."
            )
        })
    elif "256-GCM" in enc or ("GCM" in enc and "256" in key_len):
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": "AES-256-GCM (AEAD Cipher)",
            "status": "SECURE",
            "icon": "",
            "title": "Authenticated AES-256-GCM Cipher (Galois/Counter Mode)",
            "plain_english_summary": "Bank-grade 256-bit encryption that scrambles data while simultaneously attaching a 128-bit tamper-proof digital seal.",
            "detailed_explanation": (
                "Think of AES-256-GCM as placing your secret documents into an unbreakable steel vault while applying a tamper-evident holographic seal to the outside. "
                "Unlike older ciphers (like CBC) that only scramble data and require a separate process to check for tampering, GCM performs both encryption and tamper verification in a single hardware-accelerated step (RFC 4106 AEAD). "
                "If a hacker on public Wi-Fi tries to alter or inject even 1 bit of your transmitted data, the receiving server detects the broken seal and discards the packet instantly before decryption, completely stopping padding oracle attacks."
            )
        })
    elif "128-GCM" in enc or "GCM" in enc:
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": f"{enc or 'AES-128-GCM'} (AEAD Cipher)",
            "status": "SECURE",
            "icon": "",
            "title": "AES-128-GCM Authenticated Encryption (Galois/Counter Mode)",
            "plain_english_summary": "High-speed 128-bit authenticated encryption providing strong privacy and integrated tamper detection.",
            "detailed_explanation": (
                "AES-128-GCM combines fast Counter-mode data scrambling with a 128-bit Galois authentication tag (RFC 4106). "
                "It protects your connection against eavesdropping while guaranteeing that any modified or forged packets are rejected immediately."
            )
        })
    elif "256-CBC" in enc or ("CBC" in enc and "256" in key_len):
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": "AES-256-CBC (Cipher Block Chaining)",
            "status": "SECURE",
            "icon": "",
            "title": "AES-256-CBC Block Cipher (Requires External HMAC Integrity Check)",
            "plain_english_summary": "Strong 256-bit data scrambling that links data blocks together, requiring a separate hashing step to catch packet tampering.",
            "detailed_explanation": (
                "AES-256-CBC encrypts data in 128-bit chunks by chaining each chunk to the previous one (RFC 3602). "
                "While virtually impossible to crack by brute force, CBC mode only hides your data—it does not naturally check if someone modified the message in transit. "
                "Therefore, it must be paired with an external hash algorithm (like HMAC-SHA2-256) to prevent tampering."
            )
        })
    elif "128-CBC" in enc or "CBC" in enc or "AES" in enc:
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": f"{enc or 'AES-128-CBC'} (Cipher Block Chaining)",
            "status": "SECURE",
            "icon": "",
            "title": "AES-128-CBC Block Cipher Lock",
            "plain_english_summary": "Standard 128-bit block encryption for privacy protection, paired with external integrity hashing.",
            "detailed_explanation": (
                "AES-128-CBC scrambles network traffic using 128-bit secret keys. "
                "It effectively protects data privacy across untrusted networks, relying on an external HMAC hashing algorithm to catch packet tampering."
            )
        })
    elif "CHACHA" in enc or "POLY1305" in enc:
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": "ChaCha20-Poly1305 (AEAD Cipher)",
            "status": "SECURE",
            "icon": "",
            "title": "ChaCha20-Poly1305 High-Speed Stream Cipher (RFC 7634)",
            "plain_english_summary": "Ultra-fast 256-bit stream cipher optimized for mobile devices without built-in AES hardware chips.",
            "detailed_explanation": (
                "ChaCha20-Poly1305 combines Daniel J. Bernstein's ChaCha20 stream cipher with Poly1305 message authentication (RFC 7634). "
                "It delivers bank-grade 256-bit security while outperforming AES on ARM mobile processors that lack hardware acceleration, saving battery power."
            )
        })
    elif "CAMELLIA" in enc:
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": enc,
            "status": "SECURE",
            "icon": "",
            "title": f"Camellia Block Cipher ({enc} / ISO-IEC 18033-3)",
            "plain_english_summary": "International 128-bit block cipher offering military-grade privacy protection equivalent to AES.",
            "detailed_explanation": (
                "Camellia is a high-security cipher developed jointly by NTT and Mitsubishi Electric (RFC 3713). "
                "Certified by ISO/IEC and CRYPTREC, it provides mathematical strength comparable to AES."
            )
        })
    elif "NULL" in enc or "NONE" in enc:
        explanations.append({
            "parameter": "Encryption Cipher Algorithm",
            "observed_value": "NULL (Plaintext - No Encryption)",
            "status": "OBSOLETE",
            "icon": "",
            "title": "CRITICAL EXPOSURE: NULL Encryption (Raw Plaintext Transmitted)",
            "plain_english_summary": "CRITICAL RISK: Payload encryption is completely disabled—all data is transmitted in readable plain text.",
            "detailed_explanation": (
                "NULL encryption (RFC 2410) leaves data unencrypted. "
                "Any hacker or eavesdropper on the network path can perform passive wiretapping to read all transmitted passwords, business documents, and credentials."
            )
        })
    else:
        ai_card = query_gemini_explainer("Encryption Cipher Algorithm", enc or "Unknown Cipher")
        if ai_card:
            explanations.append(ai_card)
        else:
            explanations.append({
                "parameter": "Encryption Cipher Algorithm",
                "observed_value": enc if enc and enc != "UNKNOWN" else "Standard Cipher",
                "status": "INFO",
                "icon": "",
                "title": f"Data Encryption Cipher ({enc or 'Detected Cipher'})",
                "plain_english_summary": "Cryptographic algorithm responsible for obscuring readable data across public networks.",
                "detailed_explanation": f"Converts plain text into unreadable ciphertext using {enc or 'the detected cipher'} to ensure privacy."
            })

    # 3. Diffie-Hellman Key Exchange (DH Group) & Edge Cases (Hyper-Specific)
    dh = str(ipsec_info.get("dh_group", ""))
    if dh in ["19", "ECP-256"]:
        explanations.append({
            "parameter": "Diffie-Hellman Key Exchange",
            "observed_value": "DH Group 19 (NIST ECP-256)",
            "status": "SECURE",
            "icon": "",
            "title": "Elliptic Curve Diffie-Hellman Group 19 (NIST P-256 / FIPS 186-4)",
            "plain_english_summary": "Allows two remote servers across the open internet to safely agree on identical secret encryption keys without ever sending the key over the wire.",
            "detailed_explanation": (
                "Imagine two people in a room full of eavesdroppers who want to agree on a secret color. They can publicly mix base colors in a specific mathematical way so that both end up with the exact same secret color mixture, but anyone watching from the outside can never work out what the secret final color is. "
                "Diffie-Hellman Group 19 uses advanced Elliptic Curve mathematics (NIST P-256 / FIPS 186-4). "
                "It provides 128 bits of high-strength symmetric security using lightweight 256-bit key math—delivering over 10x faster connection speeds and drastically lower CPU battery consumption compared to legacy 2048-bit prime number calculations."
            )
        })
    elif dh in ["20", "ECP-384"]:
        explanations.append({
            "parameter": "Diffie-Hellman Key Exchange",
            "observed_value": "DH Group 20 (NIST ECP-384)",
            "status": "SECURE",
            "icon": "",
            "title": "High-Assurance Elliptic Curve Group 20 (NIST P-384 / NSA Suite B)",
            "plain_english_summary": "Top-tier 384-bit Elliptic Curve secret handshake meeting NSA CSfC High-Assurance government standards.",
            "detailed_explanation": (
                "DH Group 20 uses NIST P-384 prime curve math (RFC 5903). "
                "Provides a 192-bit cryptographic security margin designed for top-secret military and sovereign government VPN tunnels, offering extreme mathematical resilience against supercomputer cracking."
            )
        })
    elif dh in ["31", "CURVE448"]:
        explanations.append({
            "parameter": "Diffie-Hellman Key Exchange",
            "observed_value": "DH Group 31 (Curve448)",
            "status": "SECURE",
            "icon": "",
            "title": "Curve448 Elliptic Curve Key Exchange (RFC 8031)",
            "plain_english_summary": "Modern 448-bit Edwards-curve secret handshake offering a 224-bit security margin with complete immunity to side-channel timing attacks.",
            "detailed_explanation": (
                "DH Group 31 uses Curve448 (Goldilocks curve) specified in RFC 8031. "
                "Offers state-of-the-art protection against side-channel timing attacks with complete immunity to small-subgroup invalid curve attacks."
            )
        })
    elif dh in ["14", "MODP-2048"]:
        explanations.append({
            "parameter": "Diffie-Hellman Key Exchange",
            "observed_value": "DH Group 14 (2048-bit MODP)",
            "status": "SECURE",
            "icon": "",
            "title": "Standard Corporate Modular Prime Group 14 (2048-bit MODP / RFC 3526)",
            "plain_english_summary": "Standard enterprise key agreement using 2048-bit prime integer mathematics for shared secret creation.",
            "detailed_explanation": (
                "DH Group 14 establishes keys using a 2048-bit modular prime exponentiation group (RFC 3526). "
                "It meets current NIST SP 800-77 Rev 1 minimum enterprise compliance baselines, though modern Elliptic Curve groups (Group 19) calculate secrets much faster."
            )
        })
    elif dh in ["15", "16", "MODP-3072", "MODP-4096"]:
        explanations.append({
            "parameter": "Diffie-Hellman Key Exchange",
            "observed_value": f"DH Group {dh} (High-Bit MODP)",
            "status": "SECURE",
            "icon": "",
            "title": f"High-Bit Prime Key Exchange (DH Group {dh} / 3072+ bit MODP)",
            "plain_english_summary": "Ultra-strong key exchange using massive 3072-bit or 4096-bit prime number math.",
            "detailed_explanation": (
                f"DH Group {dh} uses large 3072-bit or 4096-bit prime numbers (RFC 3526). "
                "Provides exceptional mathematical resilience against Number Field Sieve (NFS) cracking, though requires higher CPU computation."
            )
        })
    elif dh in ["1", "2", "5", "MODP-1024"]:
        explanations.append({
            "parameter": "Diffie-Hellman Key Exchange",
            "observed_value": f"DH Group {dh} (1024-bit MODP)",
            "status": "WEAK",
            "icon": "",
            "title": f"Weak DH Group {dh} 1024-bit Key Exchange (Vulnerable to Logjam Attacks)",
            "plain_english_summary": "Underpowered 1024-bit prime key exchange vulnerable to nation-state supercomputer cracking.",
            "detailed_explanation": (
                f"DH Group {dh} relies on small 1024-bit prime numbers (RFC 2409). "
                "Security research (Logjam vulnerability / CVE-2015-4000) proved that adversaries using specialized supercomputers "
                "can precompute discrete logarithm tables to break 1024-bit handshakes and intercept secret VPN session keys."
            )
        })
    else:
        ai_card = query_gemini_explainer("Diffie-Hellman Key Exchange", f"Group {dh}" if dh else "Unknown Group")
        if ai_card:
            explanations.append(ai_card)
        else:
            explanations.append({
                "parameter": "Diffie-Hellman Key Exchange",
                "observed_value": f"Group {dh}" if dh and dh != "unknown" else "Standard Group",
                "status": "INFO",
                "icon": "",
                "title": f"Cryptographic Key Agreement (DH Group {dh if dh and dh != 'unknown' else 'Standard'})",
                "plain_english_summary": "Mathematical method allowing VPN endpoints to securely agree on session keys.",
                "detailed_explanation": f"Protects key distribution so adversaries watching network traffic cannot deduce session encryption keys for DH Group {dh}."
            })

    # 4. Perfect Forward Secrecy (PFS) (Hyper-Specific)
    pfs_val = ipsec_info.get("pfs")
    pfs_enabled = True if pfs_val in [True, "enforced", "yes"] else False
    if pfs_enabled:
        explanations.append({
            "parameter": "Perfect Forward Secrecy (PFS)",
            "observed_value": "Enforced (CREATE_CHILD_SA Rekeying)",
            "status": "SECURE",
            "icon": "",
            "title": "Ephemeral One-Time Rekeying (PFS Enforced)",
            "plain_english_summary": "Constantly generates brand-new, independent session keys so compromising today's key leaves all past and future recorded traffic 100% safe.",
            "detailed_explanation": (
                "Imagine a hotel keycard system where every single room keycard is completely unique and automatically expires after 1 hour, rather than having one master key that unlocks every room forever. "
                "Without PFS, if a hacker records your encrypted network traffic today and somehow steals your VPN server's master security key 5 years in the future, they could unlock and read every single byte of historical data they saved. "
                "With PFS enforced, your VPN server forces a fresh, one-time Diffie-Hellman mathematical secret exchange during key renegotiations (CREATE_CHILD_SA). "
                "Even if an attacker steals the master key in the future, every past session key remains mathematically isolated and completely un-decryptable."
            )
        })
    else:
        explanations.append({
            "parameter": "Perfect Forward Secrecy (PFS)",
            "observed_value": "Disabled / Static Master Derivation",
            "status": "WEAK",
            "icon": "",
            "title": "PFS Disabled (Retroactive Decryption Exposure)",
            "plain_english_summary": "CRITICAL RISK: Data session keys depend on the master server key—stealing the server key allows hackers to decrypt all recorded past traffic.",
            "detailed_explanation": (
                "Without PFS, session keys for data traffic depend directly on the main initial master key of the VPN tunnel. "
                "If an adversary records encrypted network traffic today and later compromises the VPN gateway's private key, "
                "they can retroactively decrypt all historical captured data."
            )
        })

    # 5. IPsec Encapsulation Mode (Hyper-Specific)
    mode = str(ipsec_info.get("mode", "")).capitalize()
    if mode == "Tunnel":
        explanations.append({
            "parameter": "IPsec Encapsulation Mode",
            "observed_value": "Tunnel Mode (Outer IP Wrapping)",
            "status": "SECURE",
            "icon": "",
            "title": "IPsec Tunnel Mode Encapsulation (Complete Outer IP Envelope)",
            "plain_english_summary": "Encloses your entire original IP packet—including private source and destination IP addresses—inside a brand-new encrypted outer IP envelope.",
            "detailed_explanation": (
                "Think of Transport Mode as sending a postcard where the message is written in code, but the sender and recipient home addresses are clearly visible on the outside. "
                "Tunnel Mode is like placing that entire postcard inside a thick, opaque courier envelope addressed only between two secure VPN gateways. "
                "Eavesdroppers, ISPs, or hackers monitoring public internet routers cannot see your internal company IP addresses, device names, or network architecture—they only see encrypted traffic traveling between the two public gateway endpoints."
            )
        })
    elif mode == "Transport":
        explanations.append({
            "parameter": "IPsec Encapsulation Mode",
            "observed_value": "Transport Mode (Exposed IP Headers)",
            "status": "INFO",
            "icon": "",
            "title": "IPsec Transport Mode Encapsulation (Host-to-Host Payload Shielding)",
            "plain_english_summary": "Encrypts only the inner data payload while leaving original source and destination IP addresses visible on the public network.",
            "detailed_explanation": (
                "Transport Mode inserts ESP encapsulation between the original IP header and TCP/UDP payload. "
                "It leaves original IP headers exposed for host-to-host server routing, but reveals endpoints to passive eavesdroppers."
            )
        })

    # 6. AI Machine Learning Traffic Classification (if present)
    if traffic_res and traffic_res.get("status") == "success":
        predicted_label = traffic_res.get("traffic_type", "ENCRYPTED_FLOW")
        confidence = traffic_res.get("confidence", 0.0)
        conf_pct = round(confidence * 100, 1) if confidence else 0
        explanations.append({
            "parameter": "AI Encrypted Traffic Intelligence",
            "observed_value": f"{predicted_label} ({conf_pct}% confidence)",
            "status": "SECURE" if predicted_label != "MALWARE" else "OBSOLETE",
            "icon": "",
            "title": f"AI Behavioral Pattern Recognition ({predicted_label} Application)",
            "plain_english_summary": f"Machine Learning identified the exact application activity ('{predicted_label}') inside the VPN tunnel using behavioral traffic patterns without breaking encryption.",
            "detailed_explanation": (
                f"Even though your VPN tunnel scrambles 100% of your data packets into unreadable noise, different applications leave distinct physical signatures in how they communicate. "
                f"Our trained XGBoost Machine Learning model analyzed 28 non-encrypted flow characteristics—such as packet size variations, transmission timing intervals, and bandwidth burst ratios. "
                f"Like a detective identifying a person by the cadence of their footsteps without seeing their face, the AI correctly identified your tunnel activity as '{predicted_label}' with {conf_pct}% statistical confidence, zero decryption required."
            )
        })

    # 7. Observable Metadata Exposure Intelligence (if present)
    if metadata_exposure:
        rating = metadata_exposure.get("exposure_rating", "LOW")
        score = metadata_exposure.get("exposure_score", 0)
        src_ip = metadata_exposure.get("source_ip", "N/A")
        dst_ip = metadata_exposure.get("destination_ip", "N/A")
        
        status_map = {"LOW": "SECURE", "MEDIUM": "INFO", "HIGH": "WEAK", "CRITICAL": "OBSOLETE"}
        card_status = status_map.get(rating, "INFO")
        
        explanations.append({
            "parameter": "Observable Metadata Exposure",
            "observed_value": f"{rating} Risk (Score {score}/100)",
            "status": card_status,
            "icon": "",
            "title": f"Observable Network Metadata Analysis ({src_ip or 'Endpoint'} -> {dst_ip or 'Endpoint'})",
            "plain_english_summary": f"Assessed outer IP header visibility, unencrypted IKE identity payloads, SPI correlation risk, and Transport mode exposure (Rating: {rating}).",
            "detailed_explanation": (
                f"Even when payload content is encrypted, eavesdroppers can perform side-channel traffic analysis using unencrypted metadata. "
                f"Our metadata analyzer inspected outer endpoint IP pairs ({src_ip} -> {dst_ip}), verified whether identity payloads ($ID_i$/$ID_r$) were transmitted in cleartext, "
                f"and evaluated cleartext ESP Security Parameter Index (SPI) linkability risks. Current exposure score is {score}/100."
            )
        })

    return explanations
