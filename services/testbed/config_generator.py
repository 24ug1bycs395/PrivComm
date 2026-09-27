from typing import Dict, Any, Tuple
from services.testbed.models import ScenarioDefinition, TestbedTopology


class StrongSwanConfigGenerator:
    """
    Generates strongSwan configuration artifacts (swanctl.conf or ipsec.conf / ipsec.secrets)
    for Initiator (VM1) and Responder (VM2).

    Supports:
    - Tunnel Mode and Transport Mode
    - IPv4 and IPv6 endpoint addresses
    - PFS enabled (DH group in ESP proposals) and PFS disabled (no DH group in ESP proposals)
    - AES-GCM (AEAD), AES-CBC + HMAC, 3DES, and other cipher suites
    """

    @staticmethod
    def _normalize_hash(scenario: ScenarioDefinition) -> Tuple[str, str]:
        """
        Extracts and normalizes the hash/integrity algorithm for strongSwan proposals.
        Returns a tuple of (ike_prf, esp_integrity), e.g. ('prfsha256', 'sha256').
        """
        hash_val = getattr(scenario, "hash_algorithm", None) or scenario.integrity or "SHA-256"
        h = str(hash_val).lower().replace("-", "").replace(" ", "")
        if "384" in h:
            return "prfsha384", "sha384"
        elif "512" in h:
            return "prfsha512", "sha512"
        elif "md5" in h:
            return "prfmd5", "md5"
        elif "sha1" in h:
            return "prfsha1", "sha1"
        else:
            return "prfsha256", "sha256"

    @classmethod
    def _map_ike_proposal(cls, scenario: ScenarioDefinition) -> str:
        """Maps scenario parameters and chosen hash algorithm to a strongSwan IKE proposal string."""
        enc = scenario.encryption.lower()
        prf, int_alg = cls._normalize_hash(scenario)

        if "gcm" in enc:
            if "256" in enc:
                return f"aes256gcm16-{prf}-ecp384,aes256gcm16-prfsha256-ecp256"
            else:
                return f"aes128gcm16-{prf}-ecp256,aes128gcm16-prfsha256-ecp256"
        elif "3des" in enc:
            return f"3des-{int_alg}-modp1024"
        elif "128" in enc:
            return f"aes128-{int_alg}-modp2048"
        else:
            return f"aes256-{int_alg}-modp2048"

    @classmethod
    def _map_esp_proposal(cls, scenario: ScenarioDefinition) -> str:
        """
        Maps scenario parameters and chosen hash algorithm to a strongSwan ESP proposal string.
        For AEAD ciphers (GCM), integrity is authenticated within the cipher.
        For CBC / 3DES, the integrity hash is explicitly bound into the ESP proposal.
        """
        enc = scenario.encryption.lower()
        _, int_alg = cls._normalize_hash(scenario)

        if "gcm" in enc:
            base = "aes256gcm16" if "256" in enc else "aes128gcm16"
        elif "3des" in enc:
            base = f"3des-{int_alg}"
        elif "128" in enc:
            base = f"aes128-{int_alg}"
        else:
            base = f"aes256-{int_alg}"

        if scenario.pfs:
            # Append DH group to enable PFS rekeying
            if "gcm" in enc and "256" in enc:
                return f"{base}-ecp384,{base}"
            elif "gcm" in enc:
                return f"{base}-ecp256,{base}"
            elif "3des" in enc:
                return base  # 3DES weak scenarios don't benefit from ECP
            else:
                return f"{base}-modp2048,{base}"
        else:
            # No DH group → PFS is explicitly disabled
            return base

    @classmethod
    def generate_swanctl_conf(
        cls,
        scenario: ScenarioDefinition,
        topology: TestbedTopology,
        is_initiator: bool = True
    ) -> str:
        """
        Generates modern swanctl.conf configuration for strongSwan.
        Respects ipsec_mode (tunnel/transport), ip_version (IPv4/IPv6), and pfs flag.
        """
        ike_prop = cls._map_ike_proposal(scenario)
        esp_prop = cls._map_esp_proposal(scenario)
        ike_version_num = 1 if "ikev1" in scenario.ike_version.lower() else 2

        local_ip = topology.initiator.host if is_initiator else topology.responder.host
        remote_ip = topology.responder.host if is_initiator else topology.initiator.host
        psk = scenario.pre_shared_key

        # IPv6 addresses must be wrapped in brackets for swanctl.conf
        is_ipv6 = scenario.ip_version.upper() == "IPV6"
        local_addr = f"[{local_ip}]" if is_ipv6 else local_ip
        remote_addr = f"[{remote_ip}]" if is_ipv6 else remote_ip

        rekey_time = "60s" if "rekey" in scenario.id else "1h"
        start_action = "start" if is_initiator else "none"
        mode = scenario.ipsec_mode.lower()  # "tunnel" or "transport"

        # Traffic selectors differ by mode. The Docker testbed does not create
        # separate 10.0.x.x interfaces, so tunnel mode uses the actual node
        # endpoints as /32 or /128 selectors.
        if mode == "transport":
            local_ts = "%any"
            remote_ts = "%any"
        elif is_ipv6:
            local_ts = f"{local_ip}/128"
            remote_ts = f"{remote_ip}/128"
        else:
            local_ts = f"{local_ip}/32"
            remote_ts = f"{remote_ip}/32"

        pfs_comment = "# PFS enabled: DH group included in ESP proposal" if scenario.pfs \
            else "# PFS disabled: no DH group in ESP proposal — keys derived from IKE SA"

        conf = f"""# strongSwan swanctl.conf — Generated for {scenario.name}
# Role: {"Initiator (VM1)" if is_initiator else "Responder (VM2)"}
# IPsec Mode: {mode.capitalize()} | IP Version: {scenario.ip_version}
# {pfs_comment}

connections {{
    site-to-site {{
        version = {ike_version_num}
        local_addrs = {local_ip}
        remote_addrs = {remote_ip}
        proposals = {ike_prop}
        rekey_time = {rekey_time}

        local {{
            auth = psk
            id = {local_ip}
        }}
        remote {{
            auth = psk
            id = {remote_ip}
        }}

        children {{
            net-tunnel {{
                mode = {mode}
                local_ts = {local_ts}
                remote_ts = {remote_ts}
                esp_proposals = {esp_prop}
                start_action = {start_action}
                rekey_time = {rekey_time}
            }}
        }}
    }}
}}

secrets {{
    ike-psk {{
        id-1 = {remote_ip}
        secret = "{psk}"
    }}
}}
"""
        return conf

    @classmethod
    def generate_ipsec_conf(
        cls,
        scenario: ScenarioDefinition,
        topology: TestbedTopology,
        is_initiator: bool = True
    ) -> Tuple[str, str]:
        """
        Generates legacy ipsec.conf and ipsec.secrets for strongSwan starter daemon.
        Returns: (ipsec_conf_content, ipsec_secrets_content)
        """
        ike_prop = cls._map_ike_proposal(scenario)
        esp_prop = cls._map_esp_proposal(scenario)
        ike_keyexchange = "ikev1" if "ikev1" in scenario.ike_version.lower() else "ikev2"
        aggressive = "yes" if "aggressive" in scenario.ike_version.lower() or scenario.is_weak_compliance else "no"
        mode = scenario.ipsec_mode.lower()  # "tunnel" or "transport"

        left_ip = topology.initiator.host if is_initiator else topology.responder.host
        right_ip = topology.responder.host if is_initiator else topology.initiator.host
        psk = scenario.pre_shared_key
        auto_action = "start" if is_initiator else "add"

        # Traffic selectors for legacy ipsec.conf
        if mode == "transport":
            leftsubnet = ""
            rightsubnet = ""
            subnet_lines = ""
        elif scenario.ip_version.upper() == "IPV6":
            subnet_lines = f"    leftsubnet={left_ip}/128\n    rightsubnet={right_ip}/128"
        else:
            subnet_lines = f"    leftsubnet={left_ip}/32\n    rightsubnet={right_ip}/32"

        ipsec_conf = f"""# strongSwan ipsec.conf — Scenario: {scenario.name}
# IPsec Mode: {mode.capitalize()} | IP Version: {scenario.ip_version} | PFS: {"Enabled" if scenario.pfs else "Disabled"}
config setup
    charondebug="ike 2, knl 2, cfg 2, net 2, esp 2"

conn %default
    keyexchange={ike_keyexchange}
    ike={ike_prop}!
    esp={esp_prop}!
    aggressive={aggressive}
    ikelifetime=3600s
    keylife=1800s
    rekeymargin=180s
    type={mode}

conn s2s-tunnel
    left={left_ip}
{subnet_lines}
    leftauth=psk
    right={right_ip}
    rightauth=psk
    auto={auto_action}
"""

        ipsec_secrets = f"""# strongSwan ipsec.secrets
{left_ip} {right_ip} : PSK "{psk}"
"""
        return ipsec_conf, ipsec_secrets
