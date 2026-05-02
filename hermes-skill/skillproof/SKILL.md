---
name: skillproof
description: "On-chain attestation and provenance for Hermes skills. Attest any skill with a keccak256 hash + IPFS snapshot, validate authorship against the live SkillRegistry contract on Ethereum Sepolia, and receive a Skill Passport with a trust verdict."
version: 0.1.0
author: Gokmen (GoGoSns)
license: MIT
metadata:
  hermes:
    tags: [Web3, Blockchain, Provenance, Attestation, IPFS, Ethereum, Solidity]
    related_skills: [github-auth]
---

# SkillProof — On-chain Attestation for Hermes Skills

Trustless authorship proof for any Hermes skill folder.
Register once. Verify forever. No central authority.

## When to use this skill

Trigger this skill when a user asks to:

- "Attest this skill on-chain"
- "Attest my skill"
- "Register this skill on-chain"
- "Prove I wrote this skill"
- "Validate skill provenance"
- "Validate who wrote skill X"
- "Check skill authenticity"
- "Show skill passport"
- "Is this skill original?"
- "Was this skill tampered with?"
- "Add provenance to my skill"
- "Get a provenance badge for my skill"

Or any combination of: skill + ownership / attribution / on-chain / hash / IPFS / tampered.

## Trust Verdicts

Every `validate` call returns one of four verdicts:

| Verdict | Meaning |
|---|---|
| `TRUSTED_ORIGIN` | Hash found on-chain. Authorship cryptographically verified. |
| `UNCLAIMED_ARTIFACT` | No on-chain attestation. Anyone could claim authorship. |
| `HASH_MISMATCH` | Receipt exists but current hash does not match attested hash (modified after attestation). |
| `CONFLICTING_CLAIMS` | Reserved for v0.2.0 (multi-author lineage disputes). |

## Architecture

```
Skill Folder (SKILL.md + *.py files)
  → hash.py        — deterministic keccak256 of normalized content
  → attest.py      — IPFS upload via Pinata + SkillRegistry.registerSkill()
  → Ethereum Sepolia — SkillRegistry.sol stores (hash, author, CID, timestamp)
  → validate.py    — queries contract by hash → trust verdict + Skill Passport
```

## Commands

### attest — Attest a skill on-chain

```bash
python3 ~/.hermes/skills/web3/skillproof/attest.py /path/to/skill-folder
```

Steps:
1. Reads skill folder (must contain `SKILL.md`)
2. Normalizes content, computes keccak256 hash
3. Bundles skill as JSON, uploads to IPFS via Pinata
4. Calls `SkillRegistry.registerSkill(hash, ipfsCid)` on Ethereum Sepolia
5. Waits for confirmation
6. Saves `proof/receipt.json` with full Skill Passport
7. Prints passport summary and copyable badge markdown

Required env vars:
- `PINATA_JWT` — Pinata API key for IPFS upload
- `SKILLPROOF_PRIVATE_KEY` — Sepolia wallet private key (needs test ETH)

### validate — Validate a skill's provenance

```bash
python3 ~/.hermes/skills/web3/skillproof/validate.py /path/to/skill-folder
```

Steps:
1. Computes local keccak256 hash
2. Calls `SkillRegistry.getSkill(hash)` on Ethereum Sepolia
3. Scans event logs for the registration transaction
4. Returns trust verdict + full Skill Passport
5. Saves `proof/receipt.json`

No private key required (read-only).

### hash — Compute content hash only

```bash
python3 ~/.hermes/skills/web3/skillproof/hash.py /path/to/skill-folder
```

Prints the keccak256 hash and list of files included. No network calls.

## Setup (one-time)

Copy `.env.example` to `.env` and fill in:

```dotenv
PINATA_JWT=your_pinata_jwt_here
SKILLPROOF_PRIVATE_KEY=your_sepolia_wallet_private_key_here
SKILLPROOF_RPC_URL=https://sepolia.gateway.tenderly.co
SKILLPROOF_CONTRACT_ADDRESS=0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c
```

The user needs:
- A funded Ethereum Sepolia wallet (private key for `attest` only)
- A Pinata account for IPFS upload (free tier works)

## Live Contract

- **Network**: Ethereum Sepolia (chainId: 11155111)
- **Contract**: `0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c`
- **Etherscan**: https://sepolia.etherscan.io/address/0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c

## Receipt Format

After every `attest` or `validate`, a receipt is written to `proof/receipt.json`:

```json
{
  "verdict": "TRUSTED_ORIGIN",
  "passport": {
    "identity": "<keccak256 hash>",
    "author": "<wallet address>",
    "born": "<ISO 8601 timestamp>",
    "network": "sepolia",
    "ipfsResidence": "<IPFS CID>",
    "trustLevel": "TRUSTED_ORIGIN",
    "parents": "none (original work)",
    "children": "0 forks detected"
  },
  "evidence": {
    "contractAddress": "0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c",
    "transactionHash": "<tx hash>",
    "etherscanUrl": "https://sepolia.etherscan.io/tx/<tx>",
    "ipfsGateway": "https://gateway.pinata.cloud/ipfs/<cid>",
    "blockNumber": "<block>"
  },
  "meta": {
    "toolVersion": "skillproof-v0.1.0",
    "generatedAt": "<ISO 8601>"
  }
}
```

## Limitations

- Ethereum Sepolia only (testnet for hackathon)
- Single-author model (lineage tracking planned for v0.2.0)
- `CONFLICTING_CLAIMS` verdict reserved for v0.2.0

## Author

Gokmen (GoGoSns) — Built for Nous Research Hermes Agent Creative Hackathon 2026.
