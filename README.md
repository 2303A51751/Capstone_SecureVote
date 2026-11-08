# 🗳️ Decentralized E-Voting System using Blockchain & Cryptography

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Cryptography](https://img.shields.io/badge/Crypto-ECDSA%20P--256%20%7C%20SHA3--256-orange)](https://pycryptodome.readthedocs.io/)
[![Consensus](https://img.shields.io/badge/Consensus-Proof--of--Work%20(PoW)-purple)](https://en.wikipedia.org/wiki/Proof_of_work)
[![Tests](https://img.shields.io/badge/Tests-15%2F15%20Passing-brightgreen)](home/tests.py)

An end-to-end decentralized, tamper-evident Electronic Voting System built with **Django**, **ECDSA (Elliptic Curve Digital Signatures)**, **SHA3-256 Merkle Trees**, and a **Proof-of-Work (PoW) Blockchain Ledger**.

---

## 📌 Executive Summary

Traditional centralized electronic voting systems suffer from single points of failure, lack of public verifiability, and vulnerability to insider database manipulation. 

This project solves these fundamental flaws by implementing:
1. **Cryptographic Identity & Digital Signatures**: Every voter receives a NIST P-256 ECC key pair. Ballots are digitally signed using ECDSA with SHA3-256 (FIPS 186-3 standard), guaranteeing non-repudiation and authenticity.
2. **Proof-of-Work Blockchain Consensus**: Cast votes enter a mempool and are sealed into chronologically linked blocks via Proof-of-Work (SHA3-256 cryptographic puzzle).
3. **Merkle Tree Auditing**: Every block summarizes its constituent votes into a cryptographic Merkle Root. If an attacker modifies even a single bit of a vote in the database, the Merkle root changes immediately, triggering a tamper alert.
4. **Self-Healing Distributed Consensus**: Incorporates automated consensus ledger synchronization (`sync_block`) allowing corrupted nodes to restore their state from consensus history.
5. **Seamless Demo Mode & Quick Test Suite**: Ready for live viva, academic presentations, and evaluations out-of-the-box without requiring complex email/SMTP configurations.

---



---

## 🔑 Key Cryptographic & Blockchain Specifications

| Feature | Specification | Standard / Library | Purpose |
| :--- | :--- | :--- | :--- |
| **Asymmetric Curve** | NIST P-256 (`secp256r1`) | `Crypto.PublicKey.ECC` | Voter key pair generation |
| **Digital Signature** | ECDSA (DSS) | FIPS 186-3 | Non-repudiation of cast ballots |
| **Hashing Algorithm** | SHA3-256 | `Crypto.Hash.SHA3_256` | Block hashing, ballot hashing, leaf hashing |
| **Tree Structure** | Binary Merkle Tree | `home/merkle_tool.py` | Efficient $O(\log n)$ transaction proof & tamper detection |
| **Consensus Protocol** | Proof-of-Work (PoW) | Dynamic target difficulty | Mining blocks with nonce puzzle (`000...`) |
| **Ledger Storage** | Relational / SQLite | Django ORM | Blockchain block headers, transactions, and consensus backup |

---

## ⚡ Quick Start Guide

### Prerequisites
- **Python 3.9+** (Python 3.11 recommended)
- **Git**

### Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd voting-system-using-block-chain-master
   ```

2. **(Optional) Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**:
   - **Windows One-Click (Batch)**:
     ```cmd
     run.bat
     ```
   - **Windows One-Click (PowerShell)**:
     ```powershell
     .\run.ps1
     ```
   - **Standard Terminal**:
     ```bash
     python manage.py runserver 127.0.0.1:8000
     ```

6. **Access the Application**:
   - **Voter Portal**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **Live Results**: [http://127.0.0.1:8000/show-result/](http://127.0.0.1:8000/show-result/)
   - **Proof-of-Work Miner**: [http://127.0.0.1:8000/mine-block/](http://127.0.0.1:8000/mine-block/)
   - **Blockchain Explorer**: [http://127.0.0.1:8000/blockchain/](http://127.0.0.1:8000/blockchain/)
   - **Django Administration**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🔒 Security Architecture

- **Tamper Evidence**: Block hashes include the SHA3-256 Merkle root of all transactions. Changing any ballot alters the Merkle root, invalidating the block hash.
- **Voter Non-Repudiation**: Only the owner of the private key can generate the digital signature for their ballot.
- **Vote Secrecy**: The private key is generated client-side during the voting session and is never persisted to the permanent database.
- **Self-Healing Ledger**: Dual-ledger consensus mechanism (`VoteBackup`) simulates distributed node recovery when tampering is detected.

---
