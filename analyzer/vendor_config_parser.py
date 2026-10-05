"""
Multi-Vendor Static IPsec Configuration Parser & Hardening Engine.
Supports:
- Cisco ASA / Cisco IOS-XE (IKEv1 ISAKMP / IKEv2 Crypto Maps / Transform Sets)
- Fortinet FortiOS (Phase 1 & Phase 2 IPsec Interfaces)
- pfSense / OPNsense (XML Configuration & swanctl format)
- Libreswan / Openswan (/etc/ipsec.conf)
- strongSwan (ipsec.conf & swanctl.conf)
"""

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional


class VendorConfigParser:
    """
    Parses, normalizes, audits, and generates remediation scripts for multi-vendor IPsec configs.
    """

    VENDOR_CISCO = "Cisco ASA / IOS-XE"
    VENDOR_FORTINET = "Fortinet FortiOS"
    VENDOR_PFSENSE = "pfSense / OPNsense"
    VENDOR_LIBRESWAN = "Libreswan / Openswan"
    VENDOR_STRONGSWAN = "strongSwan"
    VENDOR_UNKNOWN = "Generic / Unknown"

    @classmethod
    def detect_vendor(cls, text: str) -> str:
        """
        Auto-detect the router/firewall vendor based on syntax fingerprints.
        """
        t = text.strip()
        if "<ipsec>" in t or ("<phase1>" in t and "<dhgroup>" in t):
            return cls.VENDOR_PFSENSE
        if "config vpn ipsec" in t or "phase1-interface" in t or "set dhgrp" in t:
            return cls.VENDOR_FORTINET
        if "crypto ikev2" in t or "crypto isakmp" in t or "crypto ipsec" in t or "crypto map" in t:
            return cls.VENDOR_CISCO
        if ("ikev2=" in t or "ike=" in t) and ("conn " in t or "left=" in t):
            return cls.VENDOR_LIBRESWAN
        if "connections {" in t or "swanctl" in t or "proposals =" in t:
            return cls.VENDOR_STRONGSWAN
        if "conn " in t:
            return cls.VENDOR_LIBRESWAN
        return cls.VENDOR_UNKNOWN

    @classmethod
    def parse_config(cls, raw_text: str, override_vendor: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entrypoint: parses raw config text into normalized IPsec parameters.
        """
        vendor = override_vendor if override_vendor and override_vendor != "auto" else cls.detect_vendor(raw_text)

        if vendor == cls.VENDOR_CISCO:
            parsed = cls._parse_cisco(raw_text)
        elif vendor == cls.VENDOR_FORTINET:
            parsed = cls._parse_fortinet(raw_text)
        elif vendor == cls.VENDOR_PFSENSE:
            parsed = cls._parse_pfsense(raw_text)
        elif vendor == cls.VENDOR_LIBRESWAN:
            parsed = cls._parse_libreswan(raw_text)
        elif vendor == cls.VENDOR_STRONGSWAN:
            parsed = cls._parse_strongswan(raw_text)
        else:
            parsed = cls._parse_generic(raw_text)

        if not any(parsed.get(field) is not None for field in (
            "ike_version", "encryption", "integrity", "dh_group", "mode", "pfs",
        )):
            raise ValueError(
                f"No supported IPsec configuration fields were recognized for vendor '{vendor}'."
            )

        parsed["vendor"] = vendor
        parsed["provenance"] = "PARSED" if vendor != cls.VENDOR_UNKNOWN else "UNSUPPORTED"
        parsed["raw_config_lines"] = len(raw_text.strip().splitlines())
        parsed["field_provenance"] = {
            field: (
                "PARSED"
                if parsed.get(field) is not None and parsed.get(field) != "unknown"
                else "UNKNOWN"
            )
            for field in (
                "ike_version", "encryption", "integrity", "dh_group", "prf",
                "mode", "pfs", "source_ip", "destination_ip", "key_length",
            )
        }

        # Generate vendor-specific remediation diff
        remediation_diff = cls._generate_remediation_diff(vendor, parsed)
        parsed["remediation_config"] = remediation_diff

        return parsed

    # -------------------------------------------------------------------------
    # Vendor-Specific Parsers
    # -------------------------------------------------------------------------

    @classmethod
    def _parse_cisco(cls, text: str) -> Dict[str, Any]:
        """
        Parses Cisco IOS / ASA crypto configuration.
        """
        ike_version = None
        encryption = None
        integrity = None
        dh_group = None
        mode = None
        pfs = None
        prf = None
        remote_gw = None
        source_ip = None

        if "crypto ikev2" in text.lower() or "ikev2" in text.lower():
            ike_version = "IKEv2"
        elif "crypto isakmp" in text.lower() or "ikev1" in text.lower():
            ike_version = "IKEv1"

        # Check encryption
        if re.search(r"aes-gcm-256|esp-gcm 256|aes256-gcm|gcm-256", text, re.I):
            encryption = "AES-256-GCM"
            integrity = "AEAD"
        elif re.search(r"aes-gcm-128|esp-gcm 128|aes128-gcm", text, re.I):
            encryption = "AES-128-GCM"
            integrity = "AEAD"
        elif re.search(r"aes-256|aes 256|esp-aes 256", text, re.I):
            encryption = "AES-256-CBC"
        elif re.search(r"aes-128|aes 128|esp-aes 128", text, re.I):
            encryption = "AES-128-CBC"
        elif re.search(r"3des|esp-3des", text, re.I):
            encryption = "3DES-CBC"
        elif re.search(r"\bdes\b|esp-des", text, re.I):
            encryption = "DES-CBC"

        # Check integrity if not AEAD
        if integrity != "AEAD":
            if re.search(r"sha512|sha2-512", text, re.I):
                integrity = "HMAC-SHA2-512"
            elif re.search(r"sha384|sha2-384", text, re.I):
                integrity = "HMAC-SHA2-384"
            elif re.search(r"sha256|sha2-256|esp-sha256", text, re.I):
                integrity = "HMAC-SHA2-256"
            elif re.search(r"sha1|sha|esp-sha-hmac", text, re.I):
                integrity = "HMAC-SHA1-96"
            elif re.search(r"md5|esp-md5-hmac", text, re.I):
                integrity = "HMAC-MD5-96"

        dh_group = cls._parse_dh_group(text)

        # Check PFS
        if re.search(r"set pfs|pfs group|pfs enable", text, re.I):
            pfs = True
        elif re.search(r"no\s+set\s+pfs|pfs\s+disable", text, re.I):
            pfs = False

        # Check Mode
        if re.search(r"mode transport", text, re.I):
            mode = "Transport"
        elif re.search(r"mode tunnel", text, re.I):
            mode = "Tunnel"

        prf_match = re.search(r"\bprf\s+(sha\d+)\b", text, re.I)
        if prf_match:
            prf = prf_match.group(1).upper()

        # Check Remote Peer
        peer_match = re.search(r"set peer\s+([\d\.]+)", text, re.I)
        if peer_match:
            remote_gw = peer_match.group(1)

        return {
            "ike_version": ike_version,
            "encryption": encryption,
            "integrity": integrity,
            "dh_group": dh_group,
            "prf": prf,
            "mode": mode,
            "pfs": pfs,
            "source_ip": source_ip,
            "destination_ip": remote_gw,
            "key_length": cls._key_length(encryption)
        }

    @classmethod
    def _parse_fortinet(cls, text: str) -> Dict[str, Any]:
        """
        Parses Fortinet FortiOS VPN configuration.
        """
        ike_match = re.search(r"set ike-version\s+([12])\b", text, re.I)
        ike_version = f"IKEv{ike_match.group(1)}" if ike_match else None
        encryption = None
        integrity = None
        dh_group = None
        mode = None
        pfs = None
        remote_gw = None

        # Encryption & integrity from proposal string (e.g. set proposal aes256gcm-prfsha256 or set proposal 3des-md5)
        prop_matches = re.findall(r"set proposal\s+([^\n\r]+)", text, re.I)
        prop_str = " ".join(prop_matches) if prop_matches else text

        if re.search(r"aes256gcm|aes-gcm-256|aes256-gcm", prop_str, re.I):
            encryption = "AES-256-GCM"
            integrity = "AEAD"
        elif re.search(r"aes128gcm|aes-gcm-128", prop_str, re.I):
            encryption = "AES-128-GCM"
            integrity = "AEAD"
        elif re.search(r"aes256|aes-256", prop_str, re.I):
            encryption = "AES-256-CBC"
            integrity = "HMAC-SHA2-256" if "sha256" in prop_str.lower() else "HMAC-SHA1-96"
        elif re.search(r"3des", prop_str, re.I):
            encryption = "3DES-CBC"
            integrity = "HMAC-MD5-96" if "md5" in prop_str.lower() else "HMAC-SHA1-96"
        elif re.search(r"\bdes\b", prop_str, re.I):
            encryption = "DES-CBC"
            integrity = "HMAC-MD5-96"

        # DH Group
        dh_match = re.search(r"set dhgrp\s+([^\n\r]+)", text, re.I)
        if dh_match:
            groups = dh_match.group(1).split()
            normalized_groups = [cls._normalize_dh_group(group) for group in groups]
            if len(set(normalized_groups)) == 1:
                dh_group = normalized_groups[0]

        # PFS
        if re.search(r"set pfs\s+enable", text, re.I):
            pfs = True
        elif re.search(r"set pfs\s+disable", text, re.I):
            pfs = False

        # Encapsulation
        if re.search(r"set encapsulation\s+transport(?:-mode)?\b", text, re.I):
            mode = "Transport"
        elif re.search(r"set encapsulation\s+tunnel(?:-mode)?\b", text, re.I):
            mode = "Tunnel"

        # Remote GW
        gw_match = re.search(r"set remote-gw\s+([\d\.]+)", text, re.I)
        if gw_match:
            remote_gw = gw_match.group(1)

        return {
            "ike_version": ike_version,
            "encryption": encryption,
            "integrity": integrity,
            "dh_group": dh_group,
            "prf": cls._parse_prf(prop_str),
            "mode": mode,
            "pfs": pfs,
            "source_ip": None,
            "destination_ip": remote_gw,
            "key_length": cls._key_length(encryption)
        }

    @classmethod
    def _parse_pfsense(cls, text: str) -> Dict[str, Any]:
        """
        Parses pfSense / OPNsense XML or conf export.
        """
        ike_version = None
        encryption = None
        integrity = None
        dh_group = None
        mode = None
        pfs = None
        remote_gw = None
        prf = None

        try:
            try:
                import defusedxml.ElementTree as dET
                root = dET.fromstring(text)
            except ImportError:
                root = ET.fromstring(text)  # nosec B314
            p1 = root.find(".//phase1")
            p2 = root.find(".//phase2")

            if p1 is not None:
                iketype = p1.findtext("iketype")
                if iketype:
                    ike_version = "IKEv2" if "2" in iketype else "IKEv1"
                remote_gw = p1.findtext("remote-gateway")

                enc_algo = p1.findtext(".//encryption-algorithm/name")
                if enc_algo and "gcm" in enc_algo.lower():
                    encryption = "AES-256-GCM" if "256" in enc_algo else "AES-128-GCM"
                    integrity = "AEAD"
                elif enc_algo and "3des" in enc_algo.lower():
                    encryption = "3DES-CBC"
                elif enc_algo and "aes" in enc_algo.lower():
                    encryption = "AES-256-CBC" if "256" in enc_algo else "AES-128-CBC"

                dh = p1.findtext("dhgroup")
                if dh:
                    dh_group = cls._normalize_dh_group(dh)
                prf = p1.findtext("prf-algorithm")
            else:
                prf = None

            if p2 is not None:
                mode_text = p2.findtext("mode")
                if mode_text:
                    mode = "Transport" if "transport" in mode_text.lower() else "Tunnel"
                pfs_grp = p2.findtext("pfsgroup")
                if pfs_grp is not None:
                    pfs = pfs_grp != "0" and pfs_grp != ""
        except ET.ParseError as exc:
            if "<" in text and ">" in text:
                raise ValueError(f"Invalid pfSense/OPNsense XML: {exc}") from exc
            if "<iketype>ikev1</iketype>" in text.lower():
                ike_version = "IKEv1"
            if "3des" in text.lower():
                encryption = "3DES-CBC"
                integrity = None
            dh_m = re.search(r"<dhgroup>(\d+)</dhgroup>", text, re.I)
            if dh_m:
                dh_group = dh_m.group(1)
            prf = None

        return {
            "ike_version": ike_version,
            "encryption": encryption,
            "integrity": integrity,
            "dh_group": dh_group,
            "prf": prf,
            "mode": mode,
            "pfs": pfs,
            "source_ip": None,
            "destination_ip": remote_gw,
            "key_length": cls._key_length(encryption)
        }

    @classmethod
    def _parse_libreswan(cls, text: str) -> Dict[str, Any]:
        """
        Parses Libreswan / Openswan /etc/ipsec.conf syntax.
        """
        ike_version = None
        if re.search(r"ikev2=(no|never)", text, re.I):
            ike_version = "IKEv1"
        elif re.search(r"ikev2=(yes|insist)", text, re.I):
            ike_version = "IKEv2"

        encryption = None
        integrity = None
        dh_group = None
        mode = None
        pfs = None
        right_ip = None

        # Parse ike= and esp= parameters
        ike_match = re.search(r"ike=([^\n\r]+)", text, re.I)
        esp_match = re.search(r"esp=([^\n\r]+)", text, re.I)
        combined = f"{ike_match.group(1) if ike_match else ''} {esp_match.group(1) if esp_match else ''}"

        if re.search(r"aes_gcm256|aes_gcm_256|aes-gcm-256|aes256gcm", combined, re.I):
            encryption = "AES-256-GCM"
            integrity = "AEAD"
        elif re.search(r"aes_gcm128|aes_gcm_128|aes-gcm-128|aes128gcm", combined, re.I):
            encryption = "AES-128-GCM"
            integrity = "AEAD"
        elif re.search(r"3des", combined, re.I):
            encryption = "3DES-CBC"
            integrity = "HMAC-MD5-96" if "md5" in combined.lower() else (
                "HMAC-SHA1-96" if "sha1" in combined.lower() else None
            )
        elif re.search(r"aes256|aes_256", combined, re.I):
            encryption = "AES-256-CBC"
            integrity = "HMAC-SHA2-256" if "sha2" in combined.lower() else None

        dh_group = cls._parse_dh_group(combined)

        # PFS
        if re.search(r"pfs=(no|never)", text, re.I):
            pfs = False
        elif re.search(r"pfs=(yes|always)", text, re.I):
            pfs = True

        # Type / Mode
        if re.search(r"type=transport", text, re.I):
            mode = "Transport"
        elif re.search(r"type=tunnel", text, re.I):
            mode = "Tunnel"

        right_match = re.search(r"right=([\d\.]+)", text, re.I)
        if right_match:
            right_ip = right_match.group(1)

        return {
            "ike_version": ike_version,
            "encryption": encryption,
            "integrity": integrity,
            "dh_group": dh_group,
            "prf": cls._parse_prf(text),
            "mode": mode,
            "pfs": pfs,
            "source_ip": cls._configured_endpoint(text, "left"),
            "destination_ip": right_ip,
            "key_length": cls._key_length(encryption)
        }

    @classmethod
    def _parse_strongswan(cls, text: str) -> Dict[str, Any]:
        """
        Parses strongSwan swanctl.conf / ipsec.conf.
        """
        ike_version = None
        if re.search(r"version\s*=\s*1|keyexchange\s*=\s*ikev1", text, re.I):
            ike_version = "IKEv1"
        elif re.search(r"version\s*=\s*2|keyexchange\s*=\s*ikev2", text, re.I):
            ike_version = "IKEv2"

        encryption = None
        integrity = None
        dh_group = None
        mode = None
        pfs = None

        if re.search(r"aes256gcm|aes-gcm-256|aes_gcm", text, re.I):
            encryption = "AES-256-GCM"
            integrity = "AEAD"
        elif re.search(r"3des", text, re.I):
            encryption = "3DES-CBC"
            integrity = "HMAC-MD5-96" if "md5" in text.lower() else "HMAC-SHA1-96"
        elif re.search(r"aes256", text, re.I):
            encryption = "AES-256-CBC"
            integrity = "HMAC-SHA2-256"

        dh_group = cls._parse_dh_group(text)

        if re.search(r"mode\s*=\s*transport|type\s*=\s*transport", text, re.I):
            mode = "Transport"
        elif re.search(r"mode\s*=\s*tunnel|type\s*=\s*tunnel", text, re.I):
            mode = "Tunnel"

        pfs_match = re.search(r"pfs\s*=\s*(yes|no|always|never)", text, re.I)
        if pfs_match:
            pfs = pfs_match.group(1).lower() in {"yes", "always"}

        return {
            "ike_version": ike_version,
            "encryption": encryption,
            "integrity": integrity,
            "dh_group": dh_group,
            "prf": cls._parse_prf(text),
            "mode": mode,
            "pfs": pfs,
            "source_ip": cls._configured_endpoint(text, "local_addrs"),
            "destination_ip": cls._configured_endpoint(text, "remote_addrs"),
            "key_length": cls._key_length(encryption)
        }

    @classmethod
    def _parse_generic(cls, text: str) -> Dict[str, Any]:
        """
        Generic token search fallback.
        """
        ike_version = "IKEv2" if re.search(r"\bikev2\b", text, re.I) else (
            "IKEv1" if re.search(r"\bikev1\b", text, re.I) else None
        )
        encryption = None
        integrity = None
        if re.search(r"\bgcm\b", text, re.I):
            encryption = "AES-256-GCM" if re.search(r"256", text) else "AES-128-GCM" if re.search(r"128", text) else None
            integrity = "AEAD"
        elif re.search(r"\b3des\b", text, re.I):
            encryption = "3DES-CBC"
            integrity = "HMAC-MD5-96" if re.search(r"\bmd5\b", text, re.I) else None
        elif re.search(r"\b(aes-?256|aes256)\b", text, re.I):
            encryption = "AES-256-CBC"
            integrity = "HMAC-SHA2-256" if re.search(r"sha256", text, re.I) else None
        dh_group = cls._parse_dh_group(text)
        pfs_match = re.search(r"\bpfs\s*(?:=|\s)\s*(no|never|disable|disabled|yes|always|enable|enabled)", text, re.I)
        pfs = None if not pfs_match else pfs_match.group(1).lower() in {"yes", "always", "enable", "enabled"}
        mode = "Transport" if re.search(r"\btransport\b", text, re.I) else (
            "Tunnel" if re.search(r"\btunnel\b", text, re.I) else None
        )

        return {
            "ike_version": ike_version,
            "encryption": encryption,
            "integrity": integrity,
            "dh_group": dh_group,
            "prf": cls._parse_prf(text),
            "mode": mode,
            "pfs": pfs,
            "source_ip": None,
            "destination_ip": None,
            "key_length": cls._key_length(encryption)
        }

    # -------------------------------------------------------------------------
    # Helper & Remediation Generators
    # -------------------------------------------------------------------------

    @staticmethod
    def _key_length(encryption: Optional[str]) -> Optional[int]:
        if not encryption:
            return None
        match = re.search(r"\b(128|192|256)\b", encryption)
        if match:
            return int(match.group(1))
        if encryption.upper().startswith("3DES"):
            return 192
        if encryption.upper().startswith("DES"):
            return 64
        return None

    @staticmethod
    def _parse_prf(text: str) -> Optional[str]:
        match = re.search(r"\bprf[-_ ]?(sha(?:1|2)?[-_]?(?:256|384|512)|sha1)\b", text, re.I)
        if not match:
            return None
        raw = re.sub(r"[-_]", "", match.group(1)).upper()
        return "SHA" + raw[3:] if raw.startswith("SHA2") else raw

    @classmethod
    def _parse_dh_group(cls, text: str) -> Optional[str]:
        matches = re.findall(
            r"\b(group|dhgrp|dh|modp|ecp|curve)\s*(\d+)\b",
            text,
            re.I,
        )
        normalized = {
            cls._normalize_dh_group(
                value if prefix.lower() in {"group", "dhgrp", "dh"} else f"{prefix}{value}"
            )
            for prefix, value in matches
        }
        return normalized.pop() if len(normalized) == 1 else None

    @staticmethod
    def _configured_endpoint(text: str, key: str) -> Optional[str]:
        match = re.search(rf"^\s*{re.escape(key)}\s*=\s*([^\s#;]+)", text, re.I | re.M)
        if not match:
            return None
        value = match.group(1).strip('"\'')
        try:
            import ipaddress
            return str(ipaddress.ip_address(value))
        except ValueError:
            return None

    @classmethod
    def _normalize_dh_group(cls, val: str) -> str:
        mapping = {
            "1": "1", "2": "2", "5": "5", "14": "14", "19": "19", "20": "20", "21": "21",
            "modp768": "1", "modp1024": "2", "modp1536": "5", "modp2048": "14",
            "ecp256": "19", "ecp384": "20", "ecp521": "21", "curve25519": "31"
        }
        return mapping.get(str(val).lower(), str(val))

    @classmethod
    def _generate_remediation_diff(cls, vendor: str, parsed: Dict[str, Any]) -> str:
        """
        Generates a hardened, compliant production configuration snippet tailored
        for the specific detected vendor CLI/format.
        """
        if vendor == cls.VENDOR_CISCO:
            return (
                "! === PrivComm Hardened Cisco IOS / ASA Remediation ===\n"
                "! 1. Upgrade IKE Phase 1 to IKEv2 with AES-256-GCM & DH Group 19 (RFC 7296)\n"
                "crypto ikev2 proposal PRIVCOMM_HARDENED_PROP\n"
                " encryption aes-gcm-256\n"
                " prf sha256\n"
                " group 19 21\n"
                "!\n"
                "crypto ikev2 policy PRIVCOMM_HARDENED_POLICY\n"
                " proposal PRIVCOMM_HARDENED_PROP\n"
                "!\n"
                "! 2. Configure IKE Phase 2 IPsec with AEAD Encapsulation & PFS Enforced\n"
                "crypto ipsec transform-set HARDENED_TS esp-gcm 256\n"
                " mode tunnel\n"
                "!\n"
                "crypto ipsec profile HARDENED_PROFILE\n"
                " set transform-set HARDENED_TS\n"
                " set pfs group19\n"
                " set security-association lifetime seconds 28800\n"
            )
        elif vendor == cls.VENDOR_FORTINET:
            return (
                "# === PrivComm Hardened Fortinet FortiOS Remediation ===\n"
                "config vpn ipsec phase1-interface\n"
                "    edit \"HARDENED_VPN\"\n"
                "        set ike-version 2\n"
                "        set proposal aes256gcm-prfsha256\n"
                "        set dhgrp 19 21\n"
                "        set keylife 28800\n"
                "    next\n"
                "end\n"
                "\n"
                "config vpn ipsec phase2-interface\n"
                "    edit \"HARDENED_P2\"\n"
                "        set phase1name \"HARDENED_VPN\"\n"
                "        set proposal aes256gcm\n"
                "        set dhgrp 19\n"
                "        set pfs enable\n"
                "        set encapsulation tunnel\n"
                "        set auto-negotiate enable\n"
                "    next\n"
                "end\n"
            )
        elif vendor == cls.VENDOR_PFSENSE:
            return (
                "<!-- === PrivComm Hardened pfSense / OPNsense XML Remediation === -->\n"
                "<phase1>\n"
                "    <iketype>ikev2</iketype>\n"
                "    <encryption-algorithm>\n"
                "        <name>aes256gcm</name>\n"
                "        <keylen>256</keylen>\n"
                "    </encryption-algorithm>\n"
                "    <hash-algorithm>sha256</hash-algorithm>\n"
                "    <dhgroup>19</dhgroup>\n"
                "    <prf-algorithm>sha256</prf-algorithm>\n"
                "</phase1>\n"
                "<phase2>\n"
                "    <mode>tunnel</mode>\n"
                "    <pfsgroup>19</pfsgroup>\n"
                "    <encryption-algorithm-option>\n"
                "        <name>aes256gcm</name>\n"
                "        <keylen>256</keylen>\n"
                "    </encryption-algorithm-option>\n"
                "</phase2>\n"
            )
        elif vendor == cls.VENDOR_LIBRESWAN:
            return (
                "# === PrivComm Hardened Libreswan /etc/ipsec.conf Remediation ===\n"
                "conn Hardened-ZeroTrust-VPN\n"
                "    authby=secret\n"
                "    type=tunnel\n"
                "    ikev2=insist\n"
                "    ike=aes_gcm256-sha2_512;dh19\n"
                "    esp=aes_gcm256;dh19\n"
                "    pfs=yes\n"
                "    salifetime=8h\n"
                "    auto=start\n"
            )
        elif vendor == cls.VENDOR_STRONGSWAN:
            return (
                "# === PrivComm Hardened strongSwan Remediation ===\n"
                "connections {\n"
                "    hardened-ipsec {\n"
                "        version = 2\n"
                "        proposals = aes256gcm16-prfsha256-ecp256\n"
                "        children {\n"
                "            hardened-child {\n"
                "                mode = tunnel\n"
                "                esp_proposals = aes256gcm16-ecp256\n"
                "                dpd_action = restart\n"
                "            }\n"
                "        }\n"
                "    }\n"
                "}\n"
            )
        return None
