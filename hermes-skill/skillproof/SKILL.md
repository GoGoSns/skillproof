---
name: skillproof
description: "On-chain provenance for Hermes skills. Register skills with content hash + IPFS, verify authorship, track evolution."
version: 0.1.0
author: Gokmen (GoGoSns)
license: MIT
metadata:
  hermes:
    tags: [Web3, Blockchain, Provenance, Attribution, IPFS, Base, Solidity]
    related_skills: [github-auth]
---

# SkillProof - On-chain Provenance for Hermes Skills

This skill lets users prove they wrote a Hermes skill by registering its content hash + IPFS pointer on the Base Sepolia blockchain. Once registered, anyone can verify authorship cryptographically.

## When to use this skill

Trigger this skill when a user asks to:
- "Register this skill on-chain"
- "Prove I wrote this skill"
- "Verify who wrote skill X"
- "Add provenance to my skill"
- "Check if this skill is original"

Or when they mention any combination of: skill + ownership, skill + attribution, skill + on-chain.

## Architecture

User skill folder (any folder with SKILL.md)
  -> hash.py computes keccak256 hash of normalized content
  -> register.py uploads to IPFS via Pinata + calls smart contract
  -> SkillRegistry on Base Sepolia stores (hash, author, IPFS CID, timestamp)
  -> verify.py queries contract by hash to prove authorship

## Commands

### register - Register a new skill on-chain

bash:
python3 ~/.hermes/skills/web3/skillproof/register.py /path/to/skill-folder

What happens:
1. Reads the skill folder (must contain SKILL.md)
2. Normalizes content (strips whitespace, sorts files)
3. Computes keccak256 hash
4. Uploads skill folder to IPFS via Pinata
5. Calls SkillRegistry.registerSkill(hash, ipfsCid) on Base Sepolia
6. Prints transaction hash + IPFS CID + BaseScan link

### verify - Verify a skill's provenance

bash:
python3 ~/.hermes/skills/web3/skillproof/verify.py /path/to/skill-folder

What happens:
1. Computes hash of the skill (same way as register)
2. Queries SkillRegistry on Base Sepolia
3. Returns: author wallet address, IPFS CID, registration timestamp
4. Compares local hash vs on-chain hash

If unregistered: "Not on-chain. Anyone can claim authorship."
If registered: "Verified. Written by 0xABC...XYZ on 2026-04-30."

## Setup (one-time)

The user needs:
- A funded Base Sepolia wallet (private key in ~/.hermes/.env as SKILLPROOF_PRIVATE_KEY)
- A Pinata account (JWT in ~/.hermes/.env as PINATA_JWT)
- The deployed SkillRegistry contract address (already in code)

## Limitations

- Currently Base Sepolia only (testnet)
- Single-author model
- Evolution tracking planned for v0.2.0

## Future (post-hackathon)

- Multi-chain support
- Skill evolution chains (v1 -> v2 fork tracking)
- Optional x402 tip layer
- Reputation scoring

## Author

Gokmen (GoGoSns) - Built for Nous Research Hermes Agent Creative Hackathon 2026.

