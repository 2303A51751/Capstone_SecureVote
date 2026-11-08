# 🎓 Viva & Oral Defense Q&A Preparation Guide
## Decentralized E-Voting System using Blockchain & Cryptography

This document prepares you for technical viva, oral defense, and project evaluation questions typically asked by external examiners, professors, and technical reviewers.

---

### Q1: Why use Blockchain for electronic voting instead of a standard relational database?
**Answer**:
A traditional database (MySQL, PostgreSQL, MongoDB) has a centralized administrator (DBA) with `SUPERUSER` privileges who can perform `UPDATE` or `DELETE` operations on ballot records without cryptographic auditability. 
A **Blockchain** provides:
1. **Append-Only Immutability**: New blocks are cryptographically linked to previous block headers via cryptographic hashes ($H_k = \text{Hash}(H_{k-1} \parallel \dots)$).
2. **Tamper Evidence**: Any alteration of a historical transaction changes its Merkle root, immediately breaking the hash chain.
3. **Decentralized Verifiability**: Any citizen or external auditor can independently audit the entire ledger without trusting a centralized authority.

---

### Q2: What cryptographic algorithms are implemented in your project and why?
**Answer**:
1. **NIST P-256 (secp256r1) Elliptic Curve Cryptography**:
   - Used for voter key pair generation ($Q_A = d_A \cdot G$).
   - Provides 128-bit security level with much smaller key lengths (256-bit keys) compared to RSA (3072-bit keys), making it fast and mobile-friendly.
2. **ECDSA with DSS (FIPS 186-3)**:
   - Used for digitally signing the ballot ($UID \parallel PartyID \parallel Timestamp$).
   - Guarantees **non-repudiation** and authenticity.
3. **SHA3-256 (Keccak-based)**:
   - Used for block hashing, ballot hashing, and Merkle tree leaf hashing.
   - Resilient against length-extension attacks that affect older SHA-2 families.

---

### Q3: How is voter anonymity preserved if votes are on a public blockchain?
**Answer**:
In our system:
1. During voting, the citizen's ephemeral **NIST P-256 key pair** is generated dynamically in session memory and is never permanently coupled to their legal Aadhaar identity in the public blocks.
2. The block transactions store cryptographic ballot hashes and party selections sealed in the Merkle Tree.
3. In future extensions, **Zero-Knowledge Proofs (zk-SNARKs)** or **Ring Signatures** can be added to mathematically prove a voter belongs to the registered electoral roll without revealing which specific voter cast which ballot.

---

### Q4: What is a Merkle Tree, and what is its time complexity?
**Answer**:
A **Merkle Tree** is a binary hash tree where every leaf node is the cryptographic hash of a transaction, and every non-leaf node is the cryptographic hash of its child nodes:
$$H_{\text{parent}} = \text{SHA3-256}(H_{\text{left}} \parallel H_{\text{right}})$$
- **Verification Complexity**: $O(\log_2 N)$ hashes instead of checking all $N$ transactions.
- **Root Hash**: A single 32-byte (256-bit) string in the block header cryptographically commits all transactions in that block.

---

### Q5: How does your system detect and recover from database tampering?
**Answer**:
1. **Detection**:
   - When a block is viewed or verified, the system queries the live transactions in that block from the database and recalculates the SHA3-256 Merkle root from scratch.
   - It compares this recomputed root against the `merkle_hash` sealed in the block header at mining time.
   - If even a single bit of a vote was altered, the roots do not match, and the system flags the block with a **red Tampered status**.
2. **Self-Healing Consensus Recovery**:
   - In a distributed blockchain, honest peer nodes reject corrupted blocks and synchronize from the majority consensus chain.
   - Our system simulates this via `sync_block`: it restores the authentic transactions from the immutable consensus ledger (`VoteBackup`), recalculates the root, and returns the block to **green Verified status**.

---

### Q6: What consensus mechanism is used in this project?
**Answer**:
We implemented **Proof-of-Work (PoW)**. 
- The miner must find an integer `Nonce` such that:
  $$\text{SHA3-256}(\text{prev\_hash} \parallel \text{merkle\_root} \parallel \text{nonce} \parallel \text{timestamp})$$
  produces a hash with a target number of leading zeros (configurable via the `PUZZLE` parameter, e.g. `'000'`).
- This makes block creation computationally deliberate, preventing arbitrary or spam block production.

---

### Q7: How does the system prevent duplicate voting?
**Answer**:
Duplicate voting is prevented at two independent layers:
1. **Application Logic**: The citizen's record in `Voters` contains a boolean flag `vote_done`. Upon authenticating, if `vote_done == True`, the system halts and rejects the request.
2. **Database Integrity**: The `Vote` model uses the citizen's unique identifier (`uuid`) as its Primary Key. Any attempt to insert a second vote for the same citizen triggers a database primary key constraint violation.

---

### Q8: What is the "Mempool" in your architecture?
**Answer**:
The **Mempool** (memory pool) is the staging area for valid, digitally signed vote transactions that have been submitted by voters but have not yet been sealed into a block by the Proof-of-Work miner (`block_id = None`). Once the miner runs, it batches mempool votes, computes the Merkle Root, solves the PoW puzzle, and assigns the new `block_id` to each transaction.

---

### Q9: What happens if an attacker modifies the block's `this_hash` header directly?
**Answer**:
The blockchain is a **hash chain**. Every subsequent block $B_{k+1}$ stores `prev_hash` equal to $B_k$'s `this_hash`. If an attacker alters $B_k$'s hash, $B_{k+1}$'s `prev_hash` no longer matches, invalidating the entire subsequent blockchain history.

---

### Q10: How did you test your application?
**Answer**:
We implemented an automated test suite containing **15 unit and integration tests** in `home/tests.py` using Django's `TestCase` framework:
- **Merkle Tree Tests**: Single leaf, multi-leaf, odd leaf handling, and Merkle proof validation.
- **Cryptography Tests**: NIST P-256 key generation, valid DSS signature verification, corrupted key rejection, tampered ballot detection.
- **Voting Workflow Tests**: Valid/invalid Aadhaar authentication, OTP flow, vote creation, and duplicate vote rejection.
- **Blockchain Consensus Tests**: PoW block mining, tamper detection trigger, and consensus self-healing recovery.
All 15 tests pass with 100% success.

---

### Q11: How is the system deployed and scaled for production use?
**Answer**:
1. **WSGI Server**: Instead of the development server, production utilizes **Gunicorn** with multiple worker processes to handle concurrent requests.
2. **Static Asset Delivery**: Handled via **WhiteNoise** with compression and cache headers, eliminating external CDN dependencies.
3. **Containerization**: Configured with a multi-stage **Dockerfile** and `docker-compose.yml` for isolated cross-platform execution.
4. **Cloud PaaS**: Pre-configured for zero-downtime deployment on **Render** (via `render.yaml`) and **Railway** (via `Procfile`) with automatic HTTPS/TLS.
5. **Reverse Proxy & SSL**: On Linux VPS (Ubuntu/AWS), **Nginx** serves as an SSL termination reverse proxy forwarding requests to Gunicorn with Let's Encrypt certificates.
6. **Campus LAN Mode**: Binds to `0.0.0.0:8000` with firewall rules so evaluators and voters can access and vote from their smartphones over college Wi-Fi.

