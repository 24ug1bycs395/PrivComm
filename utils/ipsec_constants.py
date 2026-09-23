"""
IPsec and IKE Protocol Constants and Mapping Dictionaries.
Standardized according to IANA Internet Key Exchange Version 2 (IKEv2) Parameters,
RFC 7296, RFC 4301, RFC 4302, RFC 4303, RFC 8221, and NIST SP 800-77.
"""

# IKEv2 Transform Types (RFC 7296)
TRANSFORM_TYPE_ENCR = 1
TRANSFORM_TYPE_PRF = 2
TRANSFORM_TYPE_INTEG = 3
TRANSFORM_TYPE_DH = 4
TRANSFORM_TYPE_ESN = 5

# Transform Type 1 - Encryption Algorithm IDs (IKEv2 & ESP)
ENCRYPTION_ALGORITHMS = {
    1: "DES-IV64",
    2: "DES-CBC",
    3: "3DES-CBC",
    4: "RC5",
    5: "IDEA",
    6: "CAST",
    7: "Blowfish",
    8: "3IDEA",
    9: "DES-IV32",
    11: "NULL",
    12: "AES-CBC",
    13: "AES-CTR",
    14: "AES-CCM-8",
    15: "AES-CCM-12",
    16: "AES-CCM-16",
    18: "AES-GCM-8",
    19: "AES-GCM-12",
    20: "AES-GCM-16",
    28: "ChaCha20-Poly1305",
}

# Transform Type 3 - Integrity Algorithm IDs (IKEv2 & ESP/AH)
INTEGRITY_ALGORITHMS = {
    0: "NONE",
    1: "HMAC-MD5-96",
    2: "HMAC-SHA1-96",
    3: "DES-MAC",
    4: "KPDK-MD5",
    5: "AES-XCBC-96",
    6: "HMAC-MD5-128",
    7: "HMAC-SHA1-160",
    8: "AES-CMAC-96",
    9: "AES-128-GMAC",
    10: "AES-192-GMAC",
    11: "AES-256-GMAC",
    12: "HMAC-SHA2-256-128",
    13: "HMAC-SHA2-384-192",
    14: "HMAC-SHA2-512-256",
}

# Transform Type 4 - Diffie-Hellman Group IDs
DH_GROUPS = {
    0: "NONE",
    1: "1 (MODP 768-bit)",
    2: "2 (MODP 1024-bit)",
    5: "5 (MODP 1536-bit)",
    14: "14 (MODP 2048-bit)",
    15: "15 (MODP 3072-bit)",
    16: "16 (MODP 4096-bit)",
    17: "17 (MODP 6144-bit)",
    18: "18 (MODP 8192-bit)",
    19: "19 (256-bit Random ECP)",
    20: "20 (384-bit Random ECP)",
    21: "21 (521-bit Random ECP)",
    25: "25 (Curve25519)",
    26: "26 (Curve448)",
    31: "31 (Curve25519)",
}

# Extended Sequence Numbers (ESN) / Replay Protection
ESN_TYPES = {
    0: "No ESN (32-bit Sequence)",
    1: "ESN (64-bit Extended Sequence)",
}

# IKEv1 Oakley / ISAKMP Attribute Types
ISAKMP_ATTR_ENCRYPTION = 1
ISAKMP_ATTR_HASH = 2
ISAKMP_ATTR_AUTH = 3
ISAKMP_ATTR_GROUP = 4
ISAKMP_ATTR_GROUP_TYPE = 5
ISAKMP_ATTR_LIFE_TYPE = 11
ISAKMP_ATTR_LIFE_DURATION = 12
ISAKMP_ATTR_KEY_LENGTH = 14

ISAKMP_ENCRYPTION = {
    1: "DES-CBC",
    2: "IDEA-CBC",
    3: "Blowfish-CBC",
    4: "RC5-R16-B64-CBC",
    5: "3DES-CBC",
    6: "CAST-CBC",
    7: "AES-CBC",
}

ISAKMP_HASH = {
    1: "MD5",
    2: "SHA-1",
    3: "Tiger",
    4: "SHA2-256",
    5: "SHA2-384",
    6: "SHA2-512",
}
