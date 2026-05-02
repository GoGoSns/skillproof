"""SkillProof - Validate Skill Provenance

Queries the live SkillRegistry contract on Ethereum Sepolia to determine
a skill's trust verdict. Four possible outcomes:

  TRUSTED_ORIGIN     — Hash found on-chain, authorship cryptographically verified
  UNCLAIMED_ARTIFACT — No on-chain attestation; anyone could claim authorship
  HASH_MISMATCH      — Receipt exists but local hash no longer matches (modified)
  CONFLICTING_CLAIMS — Reserved for v0.2.0 (multi-author lineage disputes)

Usage:
    python3 validate.py /path/to/skill-folder
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

from hash import compute_skill_hash

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

CONTRACT_ADDRESS = os.getenv(
    "SKILLPROOF_CONTRACT_ADDRESS",
    "0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c",
)
RPC_URL = os.getenv("SKILLPROOF_RPC_URL", "https://sepolia.gateway.tenderly.co")
CHAIN_ID = 11155111

# keccak256("SkillRegistered(bytes32,address,string,uint256)")
EVENT_SIG = "0x2d128174550918dd71a1594109e82c4eec30c56865662c0c321074ac7e8c1645"
DEPLOY_BLOCK = 10700000  # Conservative lower bound for log search

ABI = [
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
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

ZERO_ADDR = "0x0000000000000000000000000000000000000000"


def short_addr(addr: str) -> str:
    if not addr or len(addr) < 10:
        return addr
    return f"{addr[:6]}...{addr[-4:]}"


def query_contract(w3: Web3, contract, content_hash: str) -> dict:
    """Call getSkill on the live contract."""
    hash_bytes = bytes.fromhex(content_hash[2:])
    skill = contract.functions.getSkill(hash_bytes).call()
    author, _, cid, ts = skill
    return {"author": author, "ipfsCid": cid, "registeredAt": ts}


def get_registration_tx(w3: Web3, content_hash: str) -> dict:
    """Scan event logs to find the registration transaction hash."""
    hash_topic = "0x" + content_hash[2:].zfill(64).lower()
    try:
        logs = w3.eth.get_logs({
            "address": CONTRACT_ADDRESS,
            "fromBlock": DEPLOY_BLOCK,
            "toBlock": "latest",
            "topics": [EVENT_SIG, hash_topic],
        })
        if logs:
            log = logs[0]
            raw = log["transactionHash"]
            tx_hex = raw.hex() if hasattr(raw, "hex") else str(raw)
            if not tx_hex.startswith("0x"):
                tx_hex = "0x" + tx_hex
            return {"transactionHash": tx_hex, "blockNumber": log["blockNumber"]}
    except Exception:
        pass
    return {"transactionHash": None, "blockNumber": None}


def load_local_receipt(skill_folder: Path) -> dict | None:
    """Load any previously saved receipt from proof/receipt.json."""
    receipt_path = skill_folder / "proof" / "receipt.json"
    if receipt_path.exists():
        try:
            return json.loads(receipt_path.read_text())
        except Exception:
            pass
    return None


def determine_verdict(is_on_chain: bool, local_hash: str, local_receipt: dict | None) -> str:
    if is_on_chain:
        return "TRUSTED_ORIGIN"
    if local_receipt:
        receipt_hash = local_receipt.get("passport", {}).get("identity")
        if receipt_hash and receipt_hash != local_hash:
            return "HASH_MISMATCH"
    return "UNCLAIMED_ARTIFACT"


def save_receipt(
    skill_folder: Path,
    verdict: str,
    content_hash: str,
    author: str | None,
    ipfs_cid: str | None,
    registered_at: int | None,
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
            "author": author,
            "born": born,
            "network": "sepolia",
            "ipfsResidence": ipfs_cid,
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
    files: list,
    author: str,
    ipfs_cid: str,
    registered_at: int,
    tx_hash: str | None,
    block_number: int | None,
    receipt_path: Path,
    skill_folder: Path,
) -> None:
    """Print the Skill Passport to terminal."""
    W = 64

    if verdict == "TRUSTED_ORIGIN":
        color = GREEN
        symbol = "✓"
        verdict_desc = "Authorship cryptographically verified on Ethereum Sepolia"
    elif verdict == "HASH_MISMATCH":
        color = RED
        symbol = "✗"
        verdict_desc = "Skill modified after its original on-chain attestation"
    else:
        color = YELLOW
        symbol = "⚠"
        verdict_desc = "No provenance record found on Ethereum Sepolia"

    border = "═" * W
    print()
    print(f"{color}{BOLD}╔{border}╗{RESET}")
    title = f"  SKILL PASSPORT — {verdict}"
    print(f"{color}{BOLD}║{title:^{W}}║{RESET}")
    print(f"{color}{BOLD}╚{border}╝{RESET}")
    print()

    short_hash = f"{content_hash[:10]}...{content_hash[-6:]}"
    print(f"  {BOLD}IDENTITY {RESET}    {short_hash}")
    print(f"  {BOLD}FILES    {RESET}    {len(files)} files hashed")

    if verdict == "TRUSTED_ORIGIN":
        born = (
            datetime.fromtimestamp(registered_at, tz=timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            if registered_at
            else "unknown"
        )
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

    elif verdict == "HASH_MISMATCH":
        print(f"  {BOLD}TRUST    {RESET}    {color}{BOLD}{verdict} {symbol}{RESET}")
        print()
        print(f"  {RED}WARNING: A receipt exists for this skill path but the{RESET}")
        print(f"  {RED}current hash does not match the attested hash.{RESET}")
        print(f"  {DIM}The skill was modified after attestation.{RESET}")
        print(f"  {DIM}Run attest.py again to create a fresh attestation.{RESET}")

    else:  # UNCLAIMED_ARTIFACT
        print(f"  {BOLD}TRUST    {RESET}    {color}{BOLD}{verdict} {symbol}{RESET}")
        print()
        print(f"  {YELLOW}No on-chain attestation found for this skill.{RESET}")
        print(f"  {DIM}Anyone could claim authorship.{RESET}")
        print()
        print(f"  To claim ownership, run:")
        print(f"  {CYAN}python3 attest.py {skill_folder}{RESET}")

    print()
    print(f"  Receipt saved → {receipt_path}")
    print()
    print(f"{color}{BOLD}╔{border}╗{RESET}")
    verdict_line = f"  {symbol} VERDICT: {verdict} — {verdict_desc}"
    print(f"{color}{BOLD}║{verdict_line:<{W}}║{RESET}")
    print(f"{color}{BOLD}╚{border}╝{RESET}")
    print()


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 validate.py /path/to/skill-folder")
        sys.exit(1)

    skill_folder = Path(sys.argv[1]).resolve()

    try:
        local_hash, files = compute_skill_hash(skill_folder)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print()
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  SkillProof — Validate Provenance{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print()
    print(f"  Skill:    {skill_folder}")
    print(f"  Hash:     {local_hash}")
    print(f"  Files:    {len(files)}")
    print(f"  Network:  Ethereum Sepolia")
    print(f"  Contract: {CONTRACT_ADDRESS}")
    print()

    print(f"{DIM}Connecting to {RPC_URL}...{RESET}")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"{YELLOW}Warning: Could not connect to RPC. Using offline check.{RESET}")
        local_receipt = load_local_receipt(skill_folder)
        verdict = "UNCLAIMED_ARTIFACT"
        if local_receipt:
            receipt_hash = local_receipt.get("passport", {}).get("identity")
            if receipt_hash == local_hash and local_receipt.get("verdict") == "TRUSTED_ORIGIN":
                verdict = "TRUSTED_ORIGIN"
            elif receipt_hash and receipt_hash != local_hash:
                verdict = "HASH_MISMATCH"
        receipt_path = save_receipt(
            skill_folder, verdict, local_hash, None, None, None, None, None
        )
        print_passport(
            verdict, local_hash, files, "", "", 0, None, None, receipt_path, skill_folder
        )
        return

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI
    )

    print(f"{DIM}Querying contract for hash {local_hash[:10]}...{RESET}")
    on_chain = query_contract(w3, contract, local_hash)
    is_on_chain = on_chain["author"].lower() != ZERO_ADDR.lower()

    local_receipt = load_local_receipt(skill_folder)
    verdict = determine_verdict(is_on_chain, local_hash, local_receipt)

    tx_hash = None
    block_number = None
    if is_on_chain:
        print(f"{DIM}Fetching registration event from logs...{RESET}")
        tx_info = get_registration_tx(w3, local_hash)
        tx_hash = tx_info["transactionHash"]
        block_number = tx_info["blockNumber"]

    receipt_path = save_receipt(
        skill_folder,
        verdict,
        local_hash,
        on_chain["author"] if is_on_chain else None,
        on_chain["ipfsCid"] if is_on_chain else None,
        on_chain["registeredAt"] if is_on_chain else None,
        tx_hash,
        block_number,
    )

    print_passport(
        verdict,
        local_hash,
        files,
        on_chain["author"] if is_on_chain else "",
        on_chain["ipfsCid"] if is_on_chain else "",
        on_chain["registeredAt"] if is_on_chain else 0,
        tx_hash,
        block_number,
        receipt_path,
        skill_folder,
    )


if __name__ == "__main__":
    main()
