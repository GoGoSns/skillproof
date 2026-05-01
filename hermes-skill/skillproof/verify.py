"""SkillProof - Verify Skill Authorship

Verifies that a Hermes skill is registered on-chain (or in mock registry
during development). Returns the author wallet, IPFS CID, and timestamp.

Usage:
    python3 verify.py /path/to/skill-folder

Output:
    - If registered: shows author, IPFS CID, registered date
    - If not registered: warning message
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from hash import compute_skill_hash
from mock_registry import get_skill, is_registered


def short_addr(addr: str) -> str:
    """Format an address as 0xABC...XYZ for display."""
    if not addr or len(addr) < 10:
        return addr
    return f"{addr[:6]}...{addr[-4:]}"


def format_timestamp(ts: int) -> str:
    """Convert unix timestamp to readable date."""
    if ts == 0:
        return "never"
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def verify_skill(skill_folder: Path) -> dict:
    """
    Verify a skill's on-chain provenance.

    Returns a dict with:
      - hash: the computed local hash
      - registered: bool
      - author, ipfsCid, registeredAt: on-chain data (if registered)
    """
    # Step 1: compute local hash
    local_hash, files = compute_skill_hash(skill_folder)

    # Step 2: query registry (mock for now, real contract later)
    skill = get_skill(local_hash)
    registered = is_registered(local_hash)

    return {
        "hash": local_hash,
        "files": files,
        "registered": registered,
        "author": skill["author"],
        "ipfsCid": skill["ipfsCid"],
        "registeredAt": skill["registeredAt"],
    }


def print_report(result: dict, skill_folder: Path):
    """Pretty-print the verification result."""
    print()
    print("=" * 60)
    print("  SkillProof Verification Report")
    print("=" * 60)
    print()
    print(f"Skill folder:    {skill_folder}")
    print(f"Files included:  {len(result['files'])}")
    for f in result["files"]:
        print(f"  - {f}")
    print()
    print(f"Local hash:      {result['hash']}")
    print()

    if result["registered"]:
        print("Status:          REGISTERED ON-CHAIN")
        print()
        print(f"  Author:        {result['author']}")
        print(f"                 ({short_addr(result['author'])})")
        print(f"  IPFS CID:      {result['ipfsCid']}")
        print(f"  Registered:    {format_timestamp(result['registeredAt'])}")
        print()
        print("  This skill has verifiable on-chain provenance.")
        print("  Authorship can be proved cryptographically.")
    else:
        print("Status:          NOT REGISTERED")
        print()
        print("  This skill has no on-chain provenance.")
        print("  Anyone could claim authorship.")
        print()
        print("  To register, run:")
        print(f"  python3 register.py {skill_folder}")

    print()
    print("=" * 60)
    print()


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 verify.py /path/to/skill-folder")
        sys.exit(1)

    skill_folder = Path(sys.argv[1]).resolve()

    try:
        result = verify_skill(skill_folder)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print_report(result, skill_folder)


if __name__ == "__main__":
    main()
