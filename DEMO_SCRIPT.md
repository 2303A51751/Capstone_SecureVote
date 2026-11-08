# 🎬 Live Viva & Evaluation Demonstration Script
## Step-by-Step 5-Minute Practical Walkthrough

This script provides an exact, step-by-step guide on what to say and what to demonstrate to the external examiners and professors during your project defense.

---

### Step 1: Launch the System & Introduce the Problem (0:00 – 1:00)

**What to Say:**
> *"Respected examiners, traditional Electronic Voting Machines (EVMs) and centralized database voting portals suffer from a critical flaw: blind trust in administrators and lack of mathematical verifiability. A database administrator can alter a vote without leaving a cryptographic trace.*
> 
> *Our project, the **SRU Blockchain E-Voting System**, solves this by implementing **NIST P-256 Elliptic Curve Digital Signatures (ECDSA)**, **SHA3-256 Binary Merkle Trees**, and a **Proof-of-Work (PoW) Blockchain Ledger**.*
> 
> *Let us demonstrate the entire voting lifecycle using our team's registered electoral roll."*

**What to Do:**
1. Double-click `run.bat` or run `py manage.py runserver 127.0.0.1:8000`.
2. Open `http://127.0.0.1:8000/` in your browser.
3. Point out the registered team members (Supreeth, Abhishek, Awez ali, Charith) on the electoral roll.

---

### Step 2: Citizen Authentication & Real-Time OTP (1:00 – 2:00)

**What to Say:**
> *"First, a citizen authenticates using their 12-digit Aadhaar UID. The backend strictly locks the session to their verified university email and issues a one-time passcode (OTP) for multi-factor authentication."*

**What to Do:**
1. Click **Supreeth** (`5403 9943 0308`) or type the 12-digit UID.
2. Click **Authenticate**. The profile table loads showing Date of Birth, Pincode, City (Hanamkonda), and registered email (`2303a51770@sru.edu.in`).
3. Point out that the email field is `readonly` and cannot be altered by an attacker.
4. Click **Send OTP**.
5. Open the email inbox on a smartphone or tab, show the live incoming email with subject `SRU Blockchain E-Voting - One-Time Passcode (OTP)`, and enter the 6-digit code.
6. Click **Verify OTP**. The green "Verified" badge appears.

---

### Step 3: Cryptographic Key Generation & Digital Signature (2:00 – 3:00)

**What to Say:**
> *"Now, the system generates a unique **NIST P-256 asymmetric cryptographic key pair** in memory. The voter's private key is used to digitally sign their ballot string $(UID \parallel Party \parallel Timestamp)$ with SHA3-256, creating an immutable ECDSA signature (FIPS 186-3).*
> 
> *This guarantees **non-repudiation**—no one can tamper with or forge the voter's choice."*

**What to Do:**
1. Click **Proceed to Vote**.
2. Select a political candidate (e.g., Bharatiya Janata Party, Congress, AAP).
3. In the confirmation dialog, explain the ECDSA private key.
4. Click **📋 Auto-Fill Private Key** (or paste the key sent to the email).
5. Click **Yes, Cast Vote**.
6. The on-screen receipt appears with the **SHA3-256 Ballot Hash** and **ECDSA Signature**.
7. Point out the notification: *"✉️ An official vote confirmation receipt with your cryptographic signature has been delivered to your registered email."*
8. Show the confirmation email in the voter's inbox containing the cryptographic receipt.

---

### Step 4: Proof-of-Work Block Mining & Mempool (3:00 – 3:45)

**What to Say:**
> *"The cast ballot is currently in the **Mempool** (unsealed transaction pool). To achieve consensus and prevent historical rewriting, transactions must be mined into a block via **Proof-of-Work (PoW)**.*
> 
> *The miner must find a nonce value such that the SHA3-256 hash of the block header satisfies our difficulty target of leading zeros (`000`)."*

**What to Do:**
1. Click **Mine Into Blockchain** (or go to `/mine-block`).
2. Point out the pending transaction count in the mempool.
3. Click **Start Mining Block**.
4. The animation runs, showing real-time nonce searches until a block hash starting with `000...` is found.
5. The block is sealed and permanently added to the blockchain ledger.

---

### Step 5: Public Blockchain Explorer, Tamper Detection & Self-Healing (3:45 – 4:30)

**What to Say:**
> *"This is our public blockchain explorer. Anyone can verify the entire election ledger. Every block summarizes its constituent votes into a **Binary Merkle Tree Root**.*
> 
> *Now, let us simulate a cyberattack where a rogue database administrator directly alters a vote in the database."*

**What to Do:**
1. Go to `/blockchain` and open the newly mined block.
2. Show that the status is **Verified (Intact)**.
3. Click **Simulate Tamper / Cyberattack**.
4. The backend alters the vote party from the chosen party to a different party.
5. Point out that the block status immediately turns **RED (Tampered)** because the live recalculation of the Merkle Tree does not match the sealed Merkle root in the block header!
6. Click **Consensus Self-Healing: Sync Block**.
7. The system synchronizes from the redundant immutable ledger (`VoteBackup`), restores the true state, and the block turns **GREEN (Verified)** again.

---

### Step 6: Live Election Results Dashboard (4:30 – 5:00)

**What to Say:**
> *"Finally, here is the live election results tally. All results are aggregated in real time directly from verified blockchain ballot records, displaying total ballots, sealed blocks, mempool status, and the winning frontrunner.*
> 
> *Our test suite of 15 automated unit tests validates the cryptographic integrity of this entire pipeline with a 100% pass rate."*

**What to Do:**
1. Click **Live Election Results** (`/show-result`).
2. Show the metrics cards (Total Ballots, Sealed in Blockchain, Pending in Mempool, Blockchain Blocks).
3. Show the dynamic progress bars and winning frontrunner banner.
4. Conclude the presentation and invite questions from the examiners.
