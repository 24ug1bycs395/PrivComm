from typing import Dict, Any, Tuple
from services.testbed.models import ScenarioDefinition, TestbedTopology


class StrongSwanConfigGenerator:
    """
    Generates strongSwan configuration artifacts (swanctl.conf or ipsec.conf / ipsec.secrets)
    for Initiator (VM1) and Responder (VM2).
    """

    @staticmethod
    def _map_crypto_proposals(scenario: ScenarioDefinition) -> Tuple[str, str]:
        """
        Maps scenario parameters to strongSwan proposal strings: (ike_proposals, esp_proposals)
        """
        enc = scenario.encryption.lower()
        if "gcm" in enc:
            # AEAD (GCM doesn't use standalone integrity in proposal)
            if "256" in enc:
                ike_p = "aes256gcm16-prfsha384-ecp384,aes256gcm16-prfsha256-ecp256"
                esp_p = "aes256gcm16-ecp384,aes256gcm16"
            else:
                ike_p = "aes128gcm16-prfsha256-ecp256"
                esp_p = "aes128gcm16"
        elif "3des" in enc:
            ike_p = "3des-md5-modp1024"
            esp_p = "3des-md5"
        elif "128" in enc:
            ike_p = "aes128-sha256-modp2048"
            esp_p = "aes128-sha256-modp2048"
        else:
            ike_p = "aes256-sha384-modp2048"
            esp_p = "aes256-sha384"

        return ike_p, esp_p

    @classmethod
    def generate_swanctl_conf(
        cls,
        scenario: ScenarioDefinition,
        topology: TestbedTopology,
        is_initiator: bool = True
    ) -> str:
        """
        Generates modern swanctl.conf configuration for strongSwan.
        """
        ike_prop, esp_prop = cls._map_crypto_proposals(scenario)
        ike_version_num = 1 if "ikev1" in scenario.ike_version.lower() else 2

        local_ip = topology.initiator.host if is_initiator else topology.responder.host
        remote_ip = topology.responder.host if is_initiator else topology.initiator.host
        psk = scenario.pre_shared_key

        rekey_time = "60s" if "rekey" in scenario.id else "1h"
        start_action = "start" if is_initiator else "none"

        conf = f"""# strongSwan swanctl.conf — Generated for {scenario.name}
# Role: {"Initiator (VM1)" if is_initiator else "Responder (VM2)"}

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
                mode = tunnel
                local_ts = 10.0.1.0/24
                remote_ts = 10.0.2.0/24
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
        ike_prop, esp_prop = cls._map_crypto_proposals(scenario)
        ike_keyexchange = "ikev1" if "ikev1" in scenario.ike_version.lower() else "ikev2"
        aggressive = "yes" if "aggressive" in scenario.ike_version.lower() or scenario.is_weak_compliance else "no"

        left_ip = topology.initiator.host if is_initiator else topology.responder.host
        right_ip = topology.responder.host if is_initiator else topology.initiator.host
        psk = scenario.pre_shared_key
        auto_action = "start" if is_initiator else "add"

        ipsec_conf = f"""# strongSwan ipsec.conf — Scenario: {scenario.name}
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
    type=tunnel

conn s2s-tunnel
    left={left_ip}
    leftsubnet=10.0.1.0/24
    leftauth=psk
    right={right_ip}
    rightsubnet=10.0.2.0/24
    rightauth=psk
    auto={auto_action}
"""

        ipsec_secrets = f"""# strongSwan ipsec.secrets
{left_ip} {right_ip} : PSK "{psk}"
"""
        return ipsec_conf, ipsec_secrets
