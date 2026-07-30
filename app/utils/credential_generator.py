import secrets
from typing import Tuple, Optional

PREFIX = "aih"

def generate_credential_pair(agent_id: str) -> Tuple[str, str, str]:
    """
    Generates a Stripe/GitHub-style two-part credential.
    Format: aih_{agent_short_id}_{lookup_nonce}_{random_secret}
    Example: aih_a3f9c1_e82a91_k7Hs92jF...
    Returns: (raw_credential_string, credential_lookup_id, random_secret)
    """
    short_id = agent_id.replace("agt_", "") if agent_id.startswith("agt_") else agent_id[:8]
    lookup_nonce = secrets.token_hex(4)  # 8 hex chars unique lookup key
    lookup_id = f"{PREFIX}_{short_id}_{lookup_nonce}"
    secret = secrets.token_urlsafe(32)
    raw_credential = f"{lookup_id}_{secret}"
    return raw_credential, lookup_id, secret

def split_credential(raw_credential: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Splits presented credential into (credential_lookup_id, secret).
    Example: 'aih_a3f9c1_e82a91_k7Hs...' -> ('aih_a3f9c1_e82a91', 'k7Hs...')
    """
    if not raw_credential or not raw_credential.startswith(f"{PREFIX}_"):
        return None, None

    parts = raw_credential.split("_")
    if len(parts) < 4:
        return None, None

    lookup_id = f"{parts[0]}_{parts[1]}_{parts[2]}"
    secret = "_".join(parts[3:])
    return lookup_id, secret
