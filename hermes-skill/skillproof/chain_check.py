import os
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from hash import compute_skill_hash

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

RPC = os.getenv("SKILLPROOF_RPC_URL")
ADDR = os.getenv("SKILLPROOF_CONTRACT_ADDRESS")
PK = os.getenv("SKILLPROOF_PRIVATE_KEY")

ABI = [
  {"inputs":[{"internalType":"bytes32","name":"contentHash","type":"bytes32"},{"internalType":"string","name":"ipfsCid","type":"string"}],"name":"registerSkill","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"bytes32","name":"contentHash","type":"bytes32"}],"name":"getSkill","outputs":[{"components":[{"internalType":"address","name":"author","type":"address"},{"internalType":"bytes32","name":"contentHash","type":"bytes32"},{"internalType":"string","name":"ipfsCid","type":"string"},{"internalType":"uint256","name":"registeredAt","type":"uint256"}],"internalType":"struct SkillRegistry.Skill","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}
]

if not RPC or not ADDR:
    raise SystemExit("Missing SKILLPROOF_RPC_URL or SKILLPROOF_CONTRACT_ADDRESS in .env")

w3 = Web3(Web3.HTTPProvider(RPC))
contract = w3.eth.contract(address=Web3.to_checksum_address(ADDR), abi=ABI)

skill_folder = HERE
content_hash, files = compute_skill_hash(skill_folder)
print("HASH:", content_hash)
print("FILES:", len(files))

skill = contract.functions.getSkill(content_hash).call()
author, _, cid, ts = skill

if author.lower() != "0x0000000000000000000000000000000000000000":
    print("✅ Already registered on-chain")
    print("Author:", author)
    print("CID:", cid)
    print("RegisteredAt:", ts)
else:
    print("ℹ️ Not registered yet.")
    if not PK:
        raise SystemExit("Missing SKILLPROOF_PRIVATE_KEY in .env")
    acct = w3.eth.account.from_key(PK)
    nonce = w3.eth.get_transaction_count(acct.address)
    tx = contract.functions.registerSkill(
        content_hash,
        "bafkreie3teph2lonn7p4ny6kf7swlxun5avt5gfob45lnmxydk5ubzq6te"
    ).build_transaction({
        "from": acct.address,
        "nonce": nonce,
        "chainId": 11155111,
        "gas": 300000,
        "maxFeePerGas": w3.to_wei("30", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("2", "gwei"),
    })
    signed = acct.sign_transaction(tx)
    txh = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("TX:", txh.hex())
    rcpt = w3.eth.wait_for_transaction_receipt(txh, timeout=180)
    print("✅ Mined in block:", rcpt.blockNumber)
