import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

from hash import compute_skill_hash

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

RPC = os.getenv("SKILLPROOF_RPC_URL", "").strip()
ADDR = os.getenv("SKILLPROOF_CONTRACT_ADDRESS", "").strip()
PK = os.getenv("SKILLPROOF_PRIVATE_KEY", "").strip()

if not RPC or not ADDR:
    raise SystemExit("❌ Missing SKILLPROOF_RPC_URL or SKILLPROOF_CONTRACT_ADDRESS in .env")

ABI = [
  {
    "inputs":[
      {"internalType":"bytes32","name":"contentHash","type":"bytes32"},
      {"internalType":"string","name":"ipfsCid","type":"string"}
    ],
    "name":"registerSkill",
    "outputs":[],
    "stateMutability":"nonpayable",
    "type":"function"
  },
  {
    "inputs":[{"internalType":"bytes32","name":"contentHash","type":"bytes32"}],
    "name":"getSkill",
    "outputs":[
      {"components":[
        {"internalType":"address","name":"author","type":"address"},
        {"internalType":"bytes32","name":"contentHash","type":"bytes32"},
        {"internalType":"string","name":"ipfsCid","type":"string"},
        {"internalType":"uint256","name":"registeredAt","type":"uint256"}
      ],"internalType":"struct SkillRegistry.Skill","name":"","type":"tuple"}
    ],
    "stateMutability":"view",
    "type":"function"
  }
]

def short(a): return a[:6] + "..." + a[-4:] if len(a) > 10 else a

w3 = Web3(Web3.HTTPProvider(RPC))
if not w3.is_connected():
    raise SystemExit(f"❌ RPC connect failed: {RPC}")

contract = w3.eth.contract(address=Web3.to_checksum_address(ADDR), abi=ABI)

skill_folder = HERE
content_hash, files = compute_skill_hash(skill_folder)

print("============================================================")
print(" SkillProof Live Check")
print("============================================================")
print(f"RPC:        {RPC}")
print(f"Contract:   {ADDR}")
print(f"Skill hash: {content_hash}")
print(f"Files:      {len(files)}")
print("------------------------------------------------------------")

skill = contract.functions.getSkill(content_hash).call()
author, _, cid, ts = skill

zero = "0x0000000000000000000000000000000000000000"
if author.lower() != zero.lower():
    print("✅ Already registered on-chain")
    print(f"Author:     {author} ({short(author)})")
    print(f"IPFS CID:   {cid}")
    print(f"Timestamp:  {ts}")
    print("============================================================")
    raise SystemExit(0)

print("ℹ️ Hash not registered yet.")
if not PK.startswith("0x") or len(PK) != 66:
    raise SystemExit("❌ SKILLPROOF_PRIVATE_KEY invalid in .env")

acct = w3.eth.account.from_key(PK)
nonce = w3.eth.get_transaction_count(acct.address)

# demo CID (istersen sonra register.py ile gerçek CID basarsın)
demo_cid = "bafkreie3teph2lonn7p4ny6kf7swlxun5avt5gfob45lnmxydk5ubzq6te"

tx = contract.functions.registerSkill(content_hash, demo_cid).build_transaction({
    "from": acct.address,
    "nonce": nonce,
    "chainId": 11155111,
    "gas": 300000,
    "maxFeePerGas": w3.to_wei("30", "gwei"),
    "maxPriorityFeePerGas": w3.to_wei("2", "gwei"),
})

signed = acct.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"🚀 Register tx: {tx_hash.hex()}")

rcpt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
print(f"✅ Mined block: {rcpt.blockNumber}")

skill2 = contract.functions.getSkill(content_hash).call()
author2, _, cid2, ts2 = skill2
print("------------------------------------------------------------")
print("✅ Verify after register")
print(f"Author:     {author2} ({short(author2)})")
print(f"IPFS CID:   {cid2}")
print(f"Timestamp:  {ts2}")
print("============================================================")
