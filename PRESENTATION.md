# 📊 Presentation Slide Deck (12 Slides)
## Decentralized E-Voting System using Blockchain & Cryptography

---

### Slide 1: Title Slide
- **Title**: Decentralized E-Voting System using Blockchain and Applied Cryptography
- **Domain**: Blockchain Technology / Information Security / Applied Cryptography
- **Institution**: SR University (SRU) — School of Computer Science & Engineering
- **Tech Stack**: Python 3.11, Django 5.2, PyCryptodome (NIST P-256, SHA3-256), SQLite, HTML5/CSS3/jQuery
- **Project Team**:
  1. Supreeth (`2303a51770@sru.edu.in`)
  2. Abhishek (`2303a51762@sru.edu.in`)
  3. Awez ali (`2303a51767@sru.edu.in`)
  4. Charith (`2303a51751@sru.edu.in`)
- **Academic Year**: 2025 – 2026

---

### Slide 2: Introduction & Motivation
- **Context**: Democratic elections are the cornerstone of governance.
- **The Challenge**: Traditional EVMs and centralized databases rely on blind trust in hardware and database administrators.
- **Why Blockchain?**:
  - Immutability: Records cannot be altered retroactively.
  - Public Audits: Anyone can verify the cryptographic chain.
  - Cryptographic Authenticity: Digital signatures guarantee genuine voter intent.

---

### Slide 3: Problem Statement
- **Centralized Single Point of Failure**: Vulnerable to insider database tampering and unauthorized SQL updates.
- **No End-to-End Verifiability**: Citizens cannot mathematically verify that their specific vote was tallied.
- **Duplicate & Sybil Attacks**: Risk of impersonation and double voting.
- **Repudiation**: Without non-repudiable digital signatures, dispute resolution is impossible.

---

### Slide 4: Project Objectives
1. Implement **NIST P-256 ECDSA** digital signatures for each ballot.
2. Build an append-only **Blockchain Ledger** with **Proof-of-Work (PoW)** consensus.
3. Construct **SHA3-256 Merkle Trees** for real-time tamper auditing.
4. Provide a **Self-Healing Distributed Consensus** mechanism to recover from corrupted node states.
5. Deliver a responsive, user-friendly election portal with live results and an explorer.

---

### Slide 5: System Architecture
- **Presentation Layer**: Voter Portal, Ballot Paper, Mining Dashboard, Blockchain Explorer, Live Tally.
- **Application Layer**: Authentication & Aadhaar verification, OTP issuance, ECDSA keypair generator, Merkle tree engine, PoW mining solver.
- **Persistence Layer**: Relational ledger (`Vote`, `Block`, `Voters`, `PoliticalParty`, `VoteBackup`).

---

### Slide 6: Cryptographic Foundation
- **Asymmetric Curve**: NIST P-256 (`secp256r1`)
  - Equation: $y^2 \equiv x^3 - 3x + b \pmod{p}$
  - Private key: $d_A \in [1, n-1]$, Public key: $Q_A = d_A \cdot G$
- **Digital Signature**: ECDSA (FIPS 186-3) over ballot string $(UID \parallel Party \parallel Timestamp)$
- **Hash Function**: SHA3-256 (Keccak sponge function)
- **Data Integrity**: $O(\log_2 N)$ binary Merkle Tree

---

### Slide 7: Voter Journey & Workflow
1. **Aadhaar UID Authentication**: Verified against registered electoral roll.
2. **OTP Verification**: Email / session passcode verification.
3. **Keypair Generation**: Ephemeral NIST P-256 key pair generated in memory.
4. **Ballot Signing**: Ballot is digitally signed with private key and verified with public key.
5. **Mempool Ingestion**: Verified vote enters transaction mempool.

---

### Slide 8: Blockchain Mining & Consensus
1. **Transaction Pool (Mempool)**: Holds unsealed signed votes.
2. **Merkle Root Calculation**: Pairwise SHA3-256 hashing of all transactions.
3. **Proof-of-Work**: Nonce search matching target difficulty (e.g. `'000'`).
   $$\text{SHA3-256}(\text{prev\_hash} \parallel \text{merkle\_root} \parallel \text{nonce} \parallel \text{timestamp}) < \text{Target}$$
4. **Block Sealing**: Block is minted, appended to chain, and transactions marked sealed.

---

### Slide 9: Live Tamper Detection & Self-Healing
- **Tamper Demonstration**:
  - Live Merkle root is recalculated from database records on demand.
  - Modifying any vote causes root mismatch: **Block turns RED ("Tampered")**.
- **Consensus Self-Healing**:
  - Clicking "Sync Block" restores authentic transactions from immutable consensus ledger (`VoteBackup`).
  - Merkle root recalculates and matches: **Block turns GREEN ("Verified")**.

---

### Slide 10: Performance, Testing & Deployment
- **Automated Tests**: 15 / 15 tests passing (100% success rate in 0.38s).
- **Execution Benchmarks**:
  - Keypair Generation: ~12 ms
  - Ballot Signature & Verification: ~4.5 ms
  - Merkle Tree Generation: < 1 ms
  - Block Mining (PoW): ~80 ms
- **System Check**: 0 issues identified in Django 5.2.
- **Production Cloud Readiness**:
  - Containerized with Docker & Docker Compose.
  - 1-click cloud PaaS deployment via Render (`render.yaml`) & Railway (`Procfile`).
  - Gunicorn WSGI server + WhiteNoise static compression engine.

---

### Slide 11: Security & Privacy Analysis
- **Non-Repudiation**: Digital signatures prevent denial of cast ballot.
- **Double-Voting Prevention**: Enforced at application logic and database primary key level.
- **Tamper Evidence**: Cryptographic hash chaining prevents retroactive ledger modification.
- **Resilience**: Node corruption is corrected via consensus synchronization.

---

### Slide 12: Conclusion & Future Enhancements
- **Summary**: Successfully built a fully functional, cryptographically secure, and auditable blockchain voting system.
- **Future Work**:
  - Zero-Knowledge Proofs (zk-SNARKs) for complete voter anonymity.
  - Homomorphic encryption for encrypted tallying.
  - Multi-node physical peer-to-peer distribution.
- **Thank You! Questions & Discussion**.

