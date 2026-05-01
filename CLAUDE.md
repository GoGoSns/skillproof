# SkillProof — CLAUDE.md

## Project Overview

**SkillProof** adds on-chain provenance to Hermes Agent skills. Any skill folder can be hashed
(deterministic keccak256), uploaded to IPFS, and registered on-chain so that authorship and
integrity can be verified trustlessly at any later time.

Built for the **Nous Research Hackathon — deadline May 3, 2026**.

Dev wallet: `0xA8DBF18e67779C7B7dC839370B85940FF506185d` (SkillProof Dev, Base Sepolia)

---

## File Structure

```
skillproof/
├── CLAUDE.md                       ← this file
├── README.md                       ← public-facing project docs
├── .gitignore
│
├── contracts/                      ← Solidity smart contracts + Hardhat project
│   ├── hardhat.config.ts           ← Hardhat 2.28 + viem plugin, Solidity 0.8.28
│   ├── package.json
│   ├── tsconfig.json
│   ├── contracts/
│   │   ├── SkillRegistry.sol       ← CORE CONTRACT: register/query skill provenance
│   │   └── Lock.sol                ← Hardhat boilerplate (ignore)
│   ├── test/
│   │   ├── SkillRegistry.ts        ← 7 tests for SkillRegistry
│   │   └── Lock.ts                 ← 8 tests for Lock (boilerplate)
│   ├── ignition/modules/
│   │   ├── Lock.ts                 ← Ignition deploy module (Hardhat boilerplate)
│   │   └── SkillRegistry.ts        ← Ignition deploy module for SkillRegistry ★
│   ├── .env.example                ← env template (PRIVATE_KEY)
│   └── artifacts/                  ← compiled ABIs + bytecode (git-ignored)
│
├── hermes-skill/                   ← Hermes skill package root
│   ├── DESCRIPTION.md              ← skill pack description for Hermes
│   └── skillproof/                 ← the actual Hermes skill
│       ├── SKILL.md                ← Hermes skill manifest (name, version, commands)
│       ├── .env                    ← secrets (Pinata JWT, private key, contract addr) — git-ignored
│       ├── .env.example            ← env template (commit this, not .env)
│       ├── hash.py                 ← compute deterministic keccak256 of a skill folder
│       ├── register.py             ← IPFS upload + mock registry write (→ real contract)
│       ├── verify.py               ← query registry and print authorship report
│       ├── mock_registry.py        ← in-memory registry for local dev / pre-deploy testing
│       └── .venv/                  ← Python 3.12 virtual environment (git-ignored)
│
├── demo/                           ← (empty) planned: Next.js dashboard + viem
└── docs/                           ← (empty) planned: additional documentation
```

### Key files in depth

| File | Purpose |
|---|---|
| `contracts/contracts/SkillRegistry.sol` | `registerSkill(bytes32 hash, string cid)` stores author + IPFS CID + timestamp. Immutable — no overwriting. |
| `hermes-skill/skillproof/hash.py` | Walks skill folder, normalizes line-endings, computes keccak256. Excludes `.venv`, `__pycache__`, `.git`, hidden files. |
| `hermes-skill/skillproof/register.py` | Calls `hash.py`, POSTs JSON bundle to Pinata, writes result to `mock_registry`. Will call real contract after deploy. |
| `hermes-skill/skillproof/verify.py` | Recomputes local hash, queries registry, prints formatted authorship report. |
| `hermes-skill/skillproof/mock_registry.py` | `dict`-backed simulation of `SkillRegistry.sol`. Used until contract is deployed. |

---

## Development Setup

**Environment:** WSL2 Ubuntu 24.04 on Windows 11.

### Node / Contracts

```bash
cd contracts
npm install          # installs Hardhat 2.28, viem plugin, etc.
```

- Node.js: Hermes bundles v22; use that or any v18+ for the contracts project.
- TypeScript is used only inside `contracts/` — all Python tooling lives in `hermes-skill/`.

### Python / Hermes Skill

```bash
cd hermes-skill/skillproof
source .venv/bin/activate     # activate the venv (Python 3.12)
```

The `.venv` is already created with the required packages:

```
eth-utils        # keccak256
requests         # Pinata HTTP calls
python-dotenv    # load .env
```

To rebuild from scratch:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install eth-utils requests python-dotenv
```

---

## Running Tests

```bash
cd contracts
npx hardhat test
```

**15 tests — all passing.**

| Suite | Count | Coverage |
|---|---|---|
| `SkillRegistry.ts` | 7 | deployment, registerSkill (new, duplicate, empty CID, zero hash), getAuthorSkillCount (zero, multiple) |
| `Lock.ts` | 8 | deployment, withdrawals (validation, permissions, success, events) |

Do not break existing tests when modifying `SkillRegistry.sol` — run the suite after every contract change.

---

## Using the Python Tools

Always activate the venv first:

```bash
cd hermes-skill/skillproof
source .venv/bin/activate
```

### hash.py — compute deterministic content hash

```bash
python3 hash.py /path/to/skill/folder
```

Prints a `0x`-prefixed keccak256 hex hash and the list of files included. Deterministic across
machines (normalizes CRLF → LF, strips trailing whitespace).

### register.py — upload to IPFS and write to registry

```bash
python3 register.py /path/to/skill/folder
```

1. Computes hash via `hash.py`
2. Bundles skill as JSON and uploads to Pinata (requires `PINATA_JWT` in `.env`)
3. Writes `{author, contentHash, ipfsCid, registeredAt}` to `mock_registry` (or real contract once deployed)

Prints the content hash, IPFS CID, and gateway URL.

### verify.py — check on-chain provenance

```bash
python3 verify.py /path/to/skill/folder
```

1. Recomputes local hash
2. Looks up hash in registry
3. Prints author wallet, IPFS CID, registration timestamp, and verification status

---

## Environment Variables

File: `hermes-skill/skillproof/.env`

```dotenv
# Required for IPFS upload (Pinata)
PINATA_JWT=<your-pinata-jwt>

# Required after contract deployment
SKILLPROOF_PRIVATE_KEY=<dev-wallet-private-key>
SKILLPROOF_CONTRACT_ADDRESS=<deployed-contract-address-on-base-sepolia>
```

**Never commit `.env` or any private key/API token to git.** The `.gitignore` excludes `.env`
already — verify before every commit.

---

## Remaining Tasks (as of May 1, 2026)

1. **Get Base Sepolia test ETH** — faucet at `https://www.alchemy.com/faucets/base-sepolia`
   (wallet: `0xA8DBF18e67779C7B7dC839370B85940FF506185d`)

2. **Deploy SkillRegistry to Base Sepolia**
   - Copy `contracts/.env.example` → `contracts/.env` and set `PRIVATE_KEY`
   - `cd contracts && npm install` (installs dotenv)
   - `npx hardhat ignition deploy ignition/modules/SkillRegistry.ts --network baseSepolia`
   - Save the deployed address to `hermes-skill/skillproof/.env` as `SKILLPROOF_CONTRACT_ADDRESS`

3. **Wire register.py and verify.py to the real contract**
   - Replace `mock_registry` calls with `viem` or `web3.py` calls to `SkillRegistry.registerSkill()`
   - Use `SKILLPROOF_PRIVATE_KEY` and `SKILLPROOF_CONTRACT_ADDRESS` from `.env`

4. **Build demo dashboard** (`demo/`)
   - Next.js + viem (not ethers.js)
   - Show: skill hash → IPFS CID → on-chain record with author + timestamp

5. **Record demo video** — show hash → register → verify flow end-to-end

6. **Submit to hackathon by May 3, 2026**

---

## Coding Conventions

### Solidity

- Version: `^0.8.28`
- License: `// SPDX-License-Identifier: MIT`
- NatSpec comments on all public functions (`/// @notice`, `/// @param`, `/// @return`)
- No upgradeable proxies — keep it simple for the hackathon scope

### Python

- Type hints on all function signatures
- Docstrings on all public functions (one-liner is fine)
- Always use the `.venv` — do not install packages globally
- `python-dotenv` for `.env` loading; never hardcode secrets

### TypeScript (contracts/)

- Use **viem** for all contract interactions — not ethers.js
- Strict TypeScript (`"strict": true` in `tsconfig.json`)
- Hardhat test helpers from `@nomicfoundation/hardhat-toolbox-viem`

### Git

Conventional commit prefixes:

| Prefix | When |
|---|---|
| `feat:` | new feature |
| `fix:` | bug fix |
| `test:` | adding or fixing tests |
| `docs:` | documentation only |
| `chore:` | build, config, tooling |
| `refactor:` | restructure without feature change |

### Security

- **Never** commit `.env`, private keys, or API tokens
- `.gitignore` covers `.env`, `.venv`, `node_modules`, `artifacts`, `__pycache__`
- Verify `git status` before every push — no secrets in the diff
