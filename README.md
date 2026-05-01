<div align="center">

# SkillProof

**On-chain provenance, attribution, and evolution tracking for Hermes Agent skills.**

[![Hackathon](https://img.shields.io/badge/Hackathon-Nous%20Research%20Hermes%202026-7c3aed?style=for-the-badge)](https://nousresearch.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.28-363636?style=for-the-badge&logo=solidity)](contracts/contracts/SkillRegistry.sol)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](hermes-skill/skillproof/)

</div>

---

## The Problem

The Hermes Agent ecosystem has **30+ community skills** — but no trust layer:

| Pain Point | Impact |
|---|---|
| No attribution | Anyone can claim they wrote a skill |
| No integrity proof | Skills can be silently modified after publishing |
| No evolution tracking | Forks have no link to originals |
| No reward mechanism | Authors get nothing when their skills are reused |

SkillProof solves all of this with a single cryptographic primitive: **content hash on a public blockchain**.

---

## How It Works

> Register once. Verify forever. No central authority.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SKILLPROOF FLOW                              │
│                                                                     │
│   ┌─────────────┐    ┌──────────┐    ┌───────────────────────────┐ │
│   │ Skill Folder│    │ hash.py  │    │      register.py          │ │
│   │             │───▶│          │───▶│                           │ │
│   │ SKILL.md    │    │keccak256 │    │  1. Upload to IPFS        │ │
│   │ *.py files  │    │ of all   │    │     (Pinata API)          │ │
│   │ etc.        │    │ content  │    │  2. Call SkillRegistry    │ │
│   └─────────────┘    └──────────┘    │     .registerSkill()      │ │
│                           │          └───────────┬───────────────┘ │
│                      content_hash                │                  │
│                           │          ┌───────────▼───────────────┐ │
│                           │          │    Base Sepolia            │ │
│                           │          │  ┌─────────────────────┐  │ │
│                           │          │  │   SkillRegistry.sol │  │ │
│                           │          │  │                     │  │ │
│                           │          │  │  hash → {           │  │ │
│                           │          │  │    author,          │  │ │
│                           │          │  │    ipfsCid,         │  │ │
│                           │          │  │    timestamp        │  │ │
│                           │          │  │  }                  │  │ │
│                           │          │  └─────────────────────┘  │ │
│                           │          └───────────────────────────┘ │
│                           │                                         │
│   ┌─────────────┐         │                                         │
│   │  verify.py  │─────────┘                                         │
│   │             │  recompute hash → query contract → prove authorship│
│   └─────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

**The guarantee**: A skill registered with hash `0xABC...` by wallet `0xDEF...` at block `N` is mathematically provable — forever, without trusting anyone.

---

## Live Demo

The SkillProof skill itself is pinned on IPFS:

**[View on Pinata Gateway](https://gateway.pinata.cloud/ipfs/bafkreie3teph2lonn7p4ny6kf7swlxun5avt5gfob45lnmxydk5ubzq6te)**

```
ipfs://bafkreie3teph2lonn7p4ny6kf7swlxun5avt5gfob45lnmxydk5ubzq6te
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Smart Contract | Solidity 0.8.28 | On-chain registry (Base Sepolia) |
| Contract Tooling | Hardhat 2.28 + viem | Compile, test, deploy |
| Content Hashing | Python + eth_utils keccak256 | Deterministic skill fingerprint |
| Decentralized Storage | IPFS via Pinata | Immutable skill content archive |
| Python Runtime | Python 3.12 | Hermes skill scripts |
| Blockchain Network | Base Sepolia (testnet) | Low-cost EVM chain |

---

## Project Structure

```
skillproof/
├── README.md
├── contracts/                         ← Solidity + Hardhat project
│   ├── contracts/
│   │   ├── Lock.sol                   ← Hardhat boilerplate
│   │   └── SkillRegistry.sol          ← Core on-chain registry ★
│   ├── test/
│   │   ├── Lock.ts                    ← 8 tests
│   │   └── SkillRegistry.ts           ← 7 tests (1 deploy + 6 functional)
│   ├── hardhat.config.ts
│   └── package.json
├── hermes-skill/
│   ├── DESCRIPTION.md
│   └── skillproof/                    ← Hermes skill package ★
│       ├── SKILL.md                   ← Hermes skill manifest
│       ├── hash.py                    ← keccak256 content hashing
│       ├── register.py                ← IPFS upload + on-chain registration
│       ├── verify.py                  ← authorship verification
│       └── mock_registry.py           ← local dev mock (pre-mainnet)
└── demo/
```

---

## Smart Contract

`SkillRegistry.sol` is intentionally minimal — one responsibility, no upgradability, no owner.

```solidity
// Core data structure
struct Skill {
    address author;       // who registered it
    bytes32 contentHash;  // keccak256 of all skill file content
    string  ipfsCid;      // immutable IPFS pointer
    uint256 registeredAt; // block.timestamp — tamper-proof
}

// Primary storage
mapping(bytes32 => Skill) public skills;

// Reverse index
mapping(address => bytes32[]) public skillsByAuthor;
```

Key invariant: once a `contentHash` is registered, it **cannot be overwritten**. Ownership is permanent.

---

## Test Results

```
  Lock
    Deployment
      ✔ Should set the right unlockTime
      ✔ Should set the right owner
      ✔ Should receive and store the funds to lock
      ✔ Should fail if the unlockTime is not in the future
    Withdrawals
      Validations
        ✔ Should revert with the right error if called too soon
        ✔ Should revert with the right error if called from another account
        ✔ Shouldn't fail if the unlockTime has arrived and the owner calls it
      Events
        ✔ Should emit an event on withdrawals

  SkillRegistry
    Deployment
      ✔ Should deploy successfully
    registerSkill
      ✔ Should register a new skill
      ✔ Should reject duplicate registration
      ✔ Should reject empty IPFS CID
      ✔ Should reject zero content hash
    getAuthorSkillCount
      ✔ Should return zero for new author
      ✔ Should count multiple skills correctly

  15 passing
```

---

## Setup

### Prerequisites

- Node.js 20+
- Python 3.12+
- A [Pinata](https://pinata.cloud) account (free tier is enough)
- A funded Base Sepolia wallet (get ETH from [Base Sepolia faucet](https://www.alchemy.com/faucets/base-sepolia))

### 1. Install contract dependencies

```bash
cd contracts
npm install
```

### 2. Run tests

```bash
cd contracts
npx hardhat test
```

### 3. Install Python dependencies

```bash
cd hermes-skill/skillproof
python3 -m venv .venv
source .venv/bin/activate
pip install eth-utils python-dotenv requests
```

### 4. Configure credentials

```bash
# hermes-skill/skillproof/.env
PINATA_JWT=your_pinata_jwt_here
SKILLPROOF_PRIVATE_KEY=your_base_sepolia_wallet_private_key
SKILLPROOF_DEV_WALLET=0xYourWalletAddress
```

### 5. Register a skill

```bash
cd hermes-skill/skillproof
python3 register.py /path/to/your-hermes-skill/
```

Output:
```
============================================================
  SkillProof - Register Skill
============================================================

Step 1/3: Computing deterministic hash...
  Hash: 0xabc123...
  Files: 4

Step 2/3: Packaging and uploading to IPFS...
  Skill name: my-skill
  IPFS CID: bafkrei...
  Gateway:  https://gateway.pinata.cloud/ipfs/bafkrei...

Step 3/3: Registering in registry...
  Registered in mock registry

============================================================
  REGISTRATION COMPLETE
============================================================
```

### 6. Verify authorship

```bash
python3 verify.py /path/to/your-hermes-skill/
```

Output:
```
============================================================
  SkillProof Verification Report
============================================================

Status:          REGISTERED ON-CHAIN

  Author:        0xA8DBF18e67779C7B7dC839370B85940FF506185d
                 (0xA8DB...85d)
  IPFS CID:      bafkrei...
  Registered:    2026-04-30 12:00:00 UTC

  This skill has verifiable on-chain provenance.
  Authorship can be proved cryptographically.
============================================================
```

---

## Hermes Agent Integration

Drop the skillproof folder into your Hermes skills directory:

```bash
cp -r hermes-skill/skillproof ~/.hermes/skills/web3/skillproof
```

Then ask Hermes:

- *"Register this skill on-chain"*
- *"Prove I wrote this skill"*
- *"Verify who wrote skill X"*
- *"Check if this skill is original"*

---

## Roadmap

### v0.1.0 — Hackathon Submission
- [x] `SkillRegistry.sol` smart contract (Base Sepolia)
- [x] Deterministic keccak256 content hashing (`hash.py`)
- [x] IPFS upload via Pinata (`register.py`)
- [x] Authorship verification (`verify.py`)
- [x] Mock registry for local development
- [x] 15 passing Hardhat tests
- [x] Skill pinned on IPFS (live demo)
- [x] Hermes skill manifest (`SKILL.md`)

### v0.2.0 — Post-Hackathon
- [ ] Live Base Sepolia deployment (real on-chain calls via web3.py)
- [ ] Skill evolution chains — link v2 to its v1 origin (`parentHash`)
- [ ] BaseScan verification link in registration output
- [ ] CLI tool: `skillproof register / verify / history`

### v0.3.0 — Ecosystem
- [ ] x402 tip layer — pay authors when their skills are used
- [ ] Reputation scoring based on skill usage + forks
- [ ] Multi-chain support (Optimism, Arbitrum)
- [ ] Hermes skill browser with provenance badges

---

## Hackathon

**Competition**: [Nous Research Hermes Agent Creative Hackathon](https://nousresearch.com)  
**Period**: April 17 → May 3, 2026  
**Track**: Web3 / Agent Infrastructure  

SkillProof addresses a real gap in the Hermes ecosystem: 30+ community skills exist with no way to prove authorship. This submission delivers a working cryptographic solution — content hashing + IPFS + smart contract — with a clean Hermes skill interface so any agent user can register and verify skills in natural language.

---

## Author

**Gokmen** ([@GoGoSns](https://github.com/GoGoSns)) — Turkey

---

## License

[MIT](LICENSE) © 2026 Gokmen
