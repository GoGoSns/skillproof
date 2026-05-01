"""SkillProof - Register Skill On-chain (with IPFS upload)

This script:
1. Computes the deterministic hash of a Hermes skill folder
2. Uploads the skill content to IPFS via Pinata
3. Records the (hash, ipfs_cid, author) in the registry

Usage:
    python3 register.py /path/to/skill-folder
"""

import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from hash import compute_skill_hash
from mock_registry import MOCK_REGISTRY, is_registered


PINATA_PIN_JSON = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")


def get_pinata_jwt():
    jwt = os.getenv("PINATA_JWT", "").strip()
    if not jwt or jwt == "PASTE_YOUR_JWT_HERE":
        print("Error: PINATA_JWT not set in .env file")
        print(f"Edit: {HERE / '.env'}")
        sys.exit(1)
    return jwt


def package_skill_as_json(skill_folder):
    files = {}
    ignore = {".venv", "__pycache__", ".git", ".env", ".DS_Store"}

    for path in sorted(skill_folder.rglob("*")):
        rel = path.relative_to(skill_folder)
        if any(part in ignore or part.startswith(".") for part in rel.parts):
            continue
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files[rel.as_posix()] = content

    skill_name = skill_folder.name
    skill_md = skill_folder / "SKILL.md"
    if skill_md.exists():
        for line in skill_md.read_text(encoding="utf-8").splitlines()[:20]:
            if line.startswith("name:"):
                skill_name = line.split(":", 1)[1].strip()
                break

    return {
        "name": skill_name,
        "files": files,
        "metadata": {
            "packagedAt": int(time.time()),
            "totalFiles": len(files),
            "tool": "skillproof-register-v0.1.0",
        },
    }


def upload_to_pinata(payload, jwt, skill_name):
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }
    body = {
        "pinataContent": payload,
        "pinataMetadata": {
            "name": f"skillproof-{skill_name}",
            "keyvalues": {"skillName": skill_name, "tool": "skillproof"},
        },
        "pinataOptions": {"cidVersion": 1},
    }

    print("  Uploading to Pinata...")
    r = requests.post(PINATA_PIN_JSON, headers=headers, json=body, timeout=30)

    if r.status_code != 200:
        print(f"Error: Pinata upload failed (HTTP {r.status_code})")
        print(f"Response: {r.text}")
        sys.exit(1)

    data = r.json()
    cid = data.get("IpfsHash") or data.get("cid")
    if not cid:
        print(f"Error: no CID in Pinata response: {data}")
        sys.exit(1)
    return cid


def register_in_registry(content_hash, author, ipfs_cid):
    if is_registered(content_hash):
        print(f"  Already registered (hash: {content_hash[:10]}...)")
        return
    MOCK_REGISTRY[content_hash] = {
        "author": author,
        "contentHash": content_hash,
        "ipfsCid": ipfs_cid,
        "registeredAt": int(time.time()),
    }
    print("  Registered in mock registry")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 register.py /path/to/skill-folder")
        sys.exit(1)

    skill_folder = Path(sys.argv[1]).resolve()
    if not skill_folder.is_dir():
        print(f"Error: not a folder: {skill_folder}")
        sys.exit(1)

    jwt = get_pinata_jwt()
    DEV_WALLET = os.getenv(
        "SKILLPROOF_DEV_WALLET",
        "0xA8DBF18e67779C7B7dC839370B85940FF506185d",
    )

    print()
    print("=" * 60)
    print("  SkillProof - Register Skill")
    print("=" * 60)
    print()
    print(f"Skill folder: {skill_folder}")
    print(f"Dev wallet:   {DEV_WALLET}")
    print()

    print("Step 1/3: Computing deterministic hash...")
    content_hash, files = compute_skill_hash(skill_folder)
    print(f"  Hash: {content_hash}")
    print(f"  Files: {len(files)}")
    print()

    print("Step 2/3: Packaging and uploading to IPFS...")
    payload = package_skill_as_json(skill_folder)
    skill_name = payload["name"]
    print(f"  Skill name: {skill_name}")
    cid = upload_to_pinata(payload, jwt, skill_name)
    print(f"  IPFS CID: {cid}")
    print(f"  Gateway:  https://gateway.pinata.cloud/ipfs/{cid}")
    print()

    print("Step 3/3: Registering in registry...")
    register_in_registry(content_hash, DEV_WALLET, cid)
    print()

    print("=" * 60)
    print("  REGISTRATION COMPLETE")
    print("=" * 60)
    print(f"Hash:      {content_hash}")
    print(f"Author:    {DEV_WALLET}")
    print(f"IPFS:      ipfs://{cid}")
    print(f"View:      https://gateway.pinata.cloud/ipfs/{cid}")
    print(f"Registry:  mock (will be on-chain after Base Sepolia deploy)")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
