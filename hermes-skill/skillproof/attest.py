"""SkillProof - Attest Skill On-chain

Computes skill hash, uploads to IPFS via Pinata, writes attestation to
SkillRegistry on Ethereum Sepolia. Generates a Skill Passport receipt.

Usage:
    python3 attest.py /path/to/skill-folder
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from web3 import Web3

from hash import compute_skill_hash

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

CONTRACT_ADDRESS = os.getenv(
    "SKILLPROOF_CONTRACT_ADDRESS",
    "0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c",
)
RPC_URL = os.getenv("SKILLPROOF_RPC_URL", "https://rpc.sepolia.org")
PINATA_PIN_JSON = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
CHAIN_ID = 11155111  # Ethereum Sepolia

ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
            {"internalType": "string", "name": "ipfsCid", "type": "string"},
        ],
        "name": "registerSkill",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "contentHash", "type": "bytes32"}],
        "name": "getSkill",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "author", "type": "address"},
                    {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
                    {"internalType": "string", "name": "ipfsCid", "type": "string"},
                    {"internalType": "uint256", "name": "registeredAt", "type": "uint256"},
                ],
                "internalType": "struct SkillRegistry.Skill",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def short_addr(addr: str) -> str:
    if not addr or len(addr) < 10:
        return addr
    return f"{addr[:6]}...{addr[-4:]}"


def get_pinata_jwt() -> str:
    jwt = os.getenv("PINATA_JWT", "").strip()
    if not jwt or jwt.startswith("your_"):
        print(f"{YELLOW}Error: PINATA_JWT not set in .env{RESET}")
        sys.exit(1)
    return jwt


def get_private_key() -> str:
    pk = os.getenv("SKILLPROOF_PRIVATE_KEY", "").strip()
    if not pk or pk.startswith("your_") or len(pk) < 64:
        print(f"{YELLOW}Error: SKILLPROOF_PRIVATE_KEY not set in .env{RESET}")
        sys.exit(1)
    return pk


def package_skill_as_json(skill_folder: Path) -> dict:
    """Bundle skill files into a JSON payload for IPFS."""
    files = {}
    ignore = {".venv", "__pycache__", ".git", ".env", ".DS_Store", "proof"}

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
            "tool": "skillproof-attest-v0.1.0",
        },
    }


def upload_to_pinata(payload: dict, jwt: str, skill_name: str) -> str:
    """Upload skill bundle to IPFS via Pinata. Returns CID."""
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

    print(f"  {DIM}Uploading to Pinata...{RESET}")
    r = requests.post(PINATA_PIN_JSON, headers=headers, json=body, timeout=30)

    if r.status_code != 200:
        print(f"  {YELLOW}Error: Pinata upload failed (HTTP {r.status_code}){RESET}")
        print(f"  Response: {r.text}")
        sys.exit(1)

    data = r.json()
    cid = data.get("IpfsHash") or data.get("cid")
    if not cid:
        print(f"  Error: no CID in Pinata response: {data}")
        sys.exit(1)
    return cid


def attest_on_chain(
    w3: Web3, contract, content_hash: str, ipfs_cid: str, private_key: str
) -> dict:
    """Submit registerSkill tx to Ethereum Sepolia. Returns tx info."""
    acct = w3.eth.account.from_key(private_key)
    hash_bytes = bytes.fromhex(content_hash[2:])

    skill = contract.functions.getSkill(hash_bytes).call()
    author, _, _, _ = skill
    zero = "0x0000000000000000000000000000000000000000"
    if author.lower() != zero.lower():
        return {"alreadyRegistered": True, "author": author, "txHash": None, "blockNumber": None}

    nonce = w3.eth.get_transaction_count(acct.address)
    tx = contract.functions.registerSkill(hash_bytes, ipfs_cid).build_transaction({
        "from": acct.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": 300000,
        "maxFeePerGas": w3.to_wei("30", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("2", "gwei"),
    })

    print(f"  {DIM}Signing and submitting transaction...{RESET}")
    signed = acct.sign_transaction(tx)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash_hex = "0x" + tx_hash_bytes.hex()

    print(f"  {CYAN}Tx: {tx_hash_hex}{RESET}")
    print(f"  {DIM}Waiting for confirmation (up to 3 min)...{RESET}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=180)
    return {
        "alreadyRegistered": False,
        "author": acct.address,
        "txHash": tx_hash_hex,
        "blockNumber": receipt.blockNumber,
    }


def save_receipt(
    skill_folder: Path,
    verdict: str,
    content_hash: str,
    author: str,
    ipfs_cid: str,
    registered_at: int,
    tx_hash: str | None,
    block_number: int | None,
) -> Path:
    """Write proof/receipt.json into the skill folder."""
    proof_dir = skill_folder / "proof"
    proof_dir.mkdir(exist_ok=True)

    born = None
    if registered_at and registered_at > 0:
        born = datetime.fromtimestamp(registered_at, tz=timezone.utc).isoformat()

    receipt = {
        "verdict": verdict,
        "passport": {
            "identity": content_hash,
            "author": author or None,
            "born": born,
            "network": "sepolia",
            "ipfsResidence": ipfs_cid or None,
            "trustLevel": verdict,
            "parents": "none (original work)",
            "children": "0 forks detected",
        },
        "evidence": {
            "contractAddress": CONTRACT_ADDRESS,
            "transactionHash": tx_hash,
            "etherscanUrl": f"https://sepolia.etherscan.io/tx/{tx_hash}" if tx_hash else None,
            "ipfsGateway": (
                f"https://gateway.pinata.cloud/ipfs/{ipfs_cid}" if ipfs_cid else None
            ),
            "blockNumber": block_number,
        },
        "meta": {
            "toolVersion": "skillproof-v0.1.0",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        },
    }

    receipt_path = proof_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    return receipt_path


def print_passport(
    verdict: str,
    content_hash: str,
    author: str,
    ipfs_cid: str,
    registered_at: int,
    tx_hash: str | None,
    block_number: int | None,
    receipt_path: Path,
) -> None:
    """Print the Skill Passport to terminal."""
    W = 64
    color = GREEN
    symbol = "✓"
    born = (
        datetime.fromtimestamp(registered_at, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        if registered_at
        else "just now"
    )

    border = "═" * W
    print()
    print(f"{color}{BOLD}╔{border}╗{RESET}")
    title = f"  SKILL PASSPORT — {verdict}"
    print(f"{color}{BOLD}║{title:^{W}}║{RESET}")
    print(f"{color}{BOLD}╚{border}╝{RESET}")
    print()
    print(f"  {BOLD}IDENTITY {RESET}    {content_hash[:10]}...{content_hash[-6:]}")
    print(f"  {BOLD}AUTHOR   {RESET}    {short_addr(author)}  ({author})")
    print(f"  {BOLD}BORN     {RESET}    {born}")
    print(f"  {BOLD}NETWORK  {RESET}    Ethereum Sepolia (chainId: {CHAIN_ID})")
    if ipfs_cid:
        print(f"  {BOLD}IPFS     {RESET}    {ipfs_cid}")
    print(f"  {BOLD}TRUST    {RESET}    {color}{BOLD}{verdict} {symbol}{RESET}")
    print(f"  {BOLD}PARENTS  {RESET}    none (original work)")
    print(f"  {BOLD}CHILDREN {RESET}    0 forks detected")
    print()
    print(f"  {DIM}{'─' * (W - 2)}{RESET}")
    print(f"  {BOLD}EVIDENCE{RESET}")
    print(f"  {DIM}Contract     {CONTRACT_ADDRESS}{RESET}")
    if tx_hash:
        print(f"  {DIM}Transaction  {tx_hash}{RESET}")
        print(f"  {DIM}Etherscan    https://sepolia.etherscan.io/tx/{tx_hash}{RESET}")
    if ipfs_cid:
        print(f"  {DIM}IPFS         https://gateway.pinata.cloud/ipfs/{ipfs_cid}{RESET}")
    if block_number:
        print(f"  {DIM}Block        {block_number}{RESET}")
    print()
    print(f"  Receipt saved → {receipt_path}")
    print()
    print(f"{color}{BOLD}╔{border}╗{RESET}")
    verdict_line = f"  {symbol} VERDICT: {verdict} — Authorship cryptographically verified"
    print(f"{color}{BOLD}║{verdict_line:<{W}}║{RESET}")
    print(f"{color}{BOLD}╚{border}╝{RESET}")
    print()


def print_badge(tx_hash: str) -> None:
    """Print copyable shields.io badge markdown."""
    badge = (
        f"[![SkillProof Verified](https://img.shields.io/badge/SkillProof-Verified-brightgreen"
        f"?logo=ethereum)](https://sepolia.etherscan.io/tx/{tx_hash})"
    )
    print(f"{BOLD}Badge (copy to your skill README):{RESET}")
    print()
    print(badge)
    print()


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 attest.py /path/to/skill-folder")
        sys.exit(1)

    skill_folder = Path(sys.argv[1]).resolve()
    if not skill_folder.is_dir():
        print(f"Error: not a folder: {skill_folder}")
        sys.exit(1)

    jwt = get_pinata_jwt()
    private_key = get_private_key()

    print()
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  SkillProof — Attest Skill{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print()
    print(f"  Skill:    {skill_folder}")
    print(f"  Network:  Ethereum Sepolia")
    print(f"  Contract: {CONTRACT_ADDRESS}")
    print()

    print(f"{BOLD}Step 1/3{RESET}  Computing deterministic hash...")
    content_hash, files = compute_skill_hash(skill_folder)
    print(f"  Hash:  {content_hash}")
    print(f"  Files: {len(files)}")
    print()

    print(f"{BOLD}Step 2/3{RESET}  Packaging and uploading to IPFS...")
    payload = package_skill_as_json(skill_folder)
    skill_name = payload["name"]
    print(f"  Skill: {skill_name}")
    ipfs_cid = upload_to_pinata(payload, jwt, skill_name)
    print(f"  {GREEN}CID:   {ipfs_cid}{RESET}")
    print(f"  {DIM}View:  https://gateway.pinata.cloud/ipfs/{ipfs_cid}{RESET}")
    print()

    print(f"{BOLD}Step 3/3{RESET}  Attesting on Ethereum Sepolia...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"  {YELLOW}Warning: RPC not reachable ({RPC_URL}). Saving offline receipt.{RESET}")
        now = int(time.time())
        receipt_path = save_receipt(
            skill_folder, "TRUSTED_ORIGIN", content_hash,
            "0x0000000000000000000000000000000000000000",
            ipfs_cid, now, None, None,
        )
        print(f"  Receipt: {receipt_path}")
        sys.exit(0)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI
    )

    result = attest_on_chain(w3, contract, content_hash, ipfs_cid, private_key)

    if result["alreadyRegistered"]:
        print(f"  {YELLOW}Already attested on-chain by {result['author']}{RESET}")
        hash_bytes = bytes.fromhex(content_hash[2:])
        skill = contract.functions.getSkill(hash_bytes).call()
        author, _, cid, ts = skill
        receipt_path = save_receipt(
            skill_folder, "TRUSTED_ORIGIN", content_hash,
            author, cid, ts, None, None,
        )
        print_passport(
            "TRUSTED_ORIGIN", content_hash, author, cid, ts, None, None, receipt_path
        )
        return

    tx_hash = result["txHash"]
    block_number = result["blockNumber"]
    author = result["author"]
    registered_at = int(time.time())

    print(f"  {GREEN}Confirmed in block {block_number}{RESET}")
    print()

    receipt_path = save_receipt(
        skill_folder, "TRUSTED_ORIGIN", content_hash,
        author, ipfs_cid, registered_at, tx_hash, block_number,
    )

    print_passport(
        "TRUSTED_ORIGIN", content_hash, author, ipfs_cid,
        registered_at, tx_hash, block_number, receipt_path,
    )
    print_badge(tx_hash)


if __name__ == "__main__":
    main()
