"""SkillProof - Mock Registry (development only)

This file simulates the on-chain SkillRegistry contract for local testing.
It will be replaced by real on-chain queries (web3.py) once the contract is
deployed to Base Sepolia.

Format matches the contract's Skill struct:
  {
    "author": "0x..." (wallet address),
    "contentHash": "0x..." (keccak256),
    "ipfsCid": "Qm..." (IPFS CID),
    "registeredAt": <unix_timestamp>
  }
"""

import time

MOCK_REGISTRY = {
    # Pre-populated for demo: a "registered" skill
    "0xdeadbeef0000000000000000000000000000000000000000000000000000beef": {
        "author": "0xA8DBF18e67779C7B7dC839370B85940FF506185d",
        "contentHash": "0xdeadbeef0000000000000000000000000000000000000000000000000000beef",
        "ipfsCid": "QmExampleMockCidForDemoOnly",
        "registeredAt": int(time.time()) - 86400,  # 1 day ago
    }
}


def get_skill(content_hash: str):
    """Mock equivalent of contract's getSkill(bytes32) function."""
    skill = MOCK_REGISTRY.get(content_hash.lower())
    if skill is None:
        # Contract returns zero-filled struct for unregistered hashes
        return {
            "author": "0x0000000000000000000000000000000000000000",
            "contentHash": "0x" + "00" * 32,
            "ipfsCid": "",
            "registeredAt": 0,
        }
    return skill


def is_registered(content_hash: str) -> bool:
    """Helper: true if this hash is on-chain (or in mock)."""
    skill = get_skill(content_hash)
    return skill["author"] != "0x0000000000000000000000000000000000000000"
