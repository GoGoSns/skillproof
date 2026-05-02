#!/usr/bin/env bash
# SkillProof — End-to-End Demo
#
# Shows the complete hash → validate → attest → validate → badge → receipt flow.
#
# Usage:
#   ./scripts/demo.sh /path/to/skill-folder
#   ./scripts/demo.sh   (defaults to hermes-skill/skillproof)

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLPROOF_DIR="$REPO_ROOT/hermes-skill/skillproof"
SKILL_DIR="${1:-$SKILLPROOF_DIR}"

# ── Header ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        SkillProof Demo — On-Chain Skill Provenance          ║"
echo "║        Nous Research Hermes Hackathon 2026                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "  Skill folder : ${CYAN}$SKILL_DIR${RESET}"
echo -e "  Contract     : ${CYAN}0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c${RESET}"
echo -e "  Network      : ${CYAN}Ethereum Sepolia${RESET}"
echo

# Activate venv
if [ -f "$SKILLPROOF_DIR/.venv/bin/activate" ]; then
    source "$SKILLPROOF_DIR/.venv/bin/activate"
fi

cd "$SKILLPROOF_DIR"

# ── Step 1: Hash ──────────────────────────────────────────────────────────────
echo -e "${BOLD}┌─ Step 1/6  Compute deterministic hash${RESET}"
echo -e "   ${YELLOW}\$ python3 hash.py \"$SKILL_DIR\"${RESET}"
echo
python3 hash.py "$SKILL_DIR"
echo

# ── Step 2: Validate (expect UNCLAIMED_ARTIFACT) ──────────────────────────────
echo -e "${BOLD}┌─ Step 2/6  Validate before attestation${RESET}"
echo -e "   ${YELLOW}Expected verdict: UNCLAIMED_ARTIFACT${RESET}"
echo -e "   ${YELLOW}\$ python3 validate.py \"$SKILL_DIR\"${RESET}"
echo
python3 validate.py "$SKILL_DIR" || true
echo

# ── Step 3: Attest ────────────────────────────────────────────────────────────
echo -e "${BOLD}┌─ Step 3/6  Attest — IPFS upload + on-chain transaction${RESET}"
echo -e "   ${YELLOW}\$ python3 attest.py \"$SKILL_DIR\"${RESET}"
echo
python3 attest.py "$SKILL_DIR"
echo

# ── Step 4: Validate (expect TRUSTED_ORIGIN) ─────────────────────────────────
echo -e "${BOLD}┌─ Step 4/6  Validate after attestation${RESET}"
echo -e "   ${YELLOW}Expected verdict: TRUSTED_ORIGIN${RESET}"
echo -e "   ${YELLOW}\$ python3 validate.py \"$SKILL_DIR\"${RESET}"
echo
python3 validate.py "$SKILL_DIR"
echo

# ── Step 5: Badge ─────────────────────────────────────────────────────────────
echo -e "${BOLD}┌─ Step 5/6  Badge Markdown${RESET}"
echo -e "   ${GREEN}Copy this to your skill README:${RESET}"
echo
RECEIPT_FILE="$SKILL_DIR/proof/receipt.json"
if [ -f "$RECEIPT_FILE" ]; then
    TX=$(python3 -c "import json; d=json.load(open('$RECEIPT_FILE')); print(d['evidence'].get('transactionHash') or '')" 2>/dev/null || true)
    if [ -n "$TX" ] && [ "$TX" != "None" ]; then
        echo "[![SkillProof Verified](https://img.shields.io/badge/SkillProof-Verified-brightgreen?logo=ethereum)](https://sepolia.etherscan.io/tx/$TX)"
    else
        echo "[![SkillProof Verified](https://img.shields.io/badge/SkillProof-Verified-brightgreen?logo=ethereum)](https://sepolia.etherscan.io/address/0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c)"
    fi
else
    echo "[![SkillProof Verified](https://img.shields.io/badge/SkillProof-Verified-brightgreen?logo=ethereum)](https://sepolia.etherscan.io/address/0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c)"
fi
echo

# ── Step 6: Receipt ───────────────────────────────────────────────────────────
echo -e "${BOLD}┌─ Step 6/6  Receipt${RESET}"
if [ -f "$RECEIPT_FILE" ]; then
    echo -e "   ${GREEN}Saved at: $RECEIPT_FILE${RESET}"
    echo
    python3 -c "import json; print(json.dumps(json.load(open('$RECEIPT_FILE')), indent=2))"
else
    echo -e "   ${YELLOW}No receipt found at $RECEIPT_FILE${RESET}"
fi
echo

# ── Footer ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Demo complete.                                             ║"
echo "║                                                             ║"
echo "║  Live contract:                                             ║"
echo "║  sepolia.etherscan.io/address/                              ║"
echo "║  0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
