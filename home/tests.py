from django.test import TestCase, Client
from django.utils import timezone
from django.conf import settings
from .models import Voters, PoliticalParty, Vote, VoteBackup, Block, MiningInfo
from .merkle_tool import MerkleTools
from .methods_module import generate_keys, verify_vote, send_email_otp, vote_count
from Crypto.Hash import SHA3_256
import datetime

class MerkleTreeTests(TestCase):
    """
    Tests SHA3-256 Merkle Tree calculation, proof generation, and verification.
    """
    def test_single_leaf_root(self):
        tree = MerkleTools()
        tree.add_leaf("single-transaction", do_hash=True)
        tree.make_tree()
        root = tree.get_merkle_root()
        expected = SHA3_256.new("single-transaction".encode('utf-8')).hexdigest()
        self.assertEqual(root, expected)

    def test_multi_leaves_root(self):
        tree = MerkleTools()
        leaves = ["tx1", "tx2", "tx3", "tx4"]
        tree.add_leaf(leaves, do_hash=True)
        tree.make_tree()
        self.assertTrue(tree.get_tree_ready_state())
        self.assertEqual(tree.get_leaf_count(), 4)
        root = tree.get_merkle_root()
        self.assertIsNotNone(root)
        self.assertEqual(len(root), 64)

    def test_merkle_proof_validation(self):
        tree = MerkleTools()
        leaves = ["vote-alice", "vote-bob", "vote-charlie"]
        tree.add_leaf(leaves, do_hash=True)
        tree.make_tree()
        root = tree.get_merkle_root()

        for idx in range(3):
            proof = tree.get_proof(idx)
            leaf_hash = tree.get_leaf(idx)
            is_valid = tree.validate_proof(proof, leaf_hash, root)
            self.assertTrue(is_valid, f"Proof for leaf index {idx} failed validation")

class CryptographyTests(TestCase):
    """
    Tests NIST P-256 ECC digital signatures and SHA3-256 hashing.
    """
    def test_keypair_generation(self):
        private_key, public_key = generate_keys()
        self.assertIn("-----BEGIN PRIVATE KEY-----", private_key)
        self.assertIn("-----BEGIN PUBLIC KEY-----", public_key)

    def test_valid_ballot_signature(self):
        private_key, public_key = generate_keys()
        ballot = "100000000001|bjp|1600000000.0"
        result = verify_vote(private_key, public_key, ballot)
        self.assertTrue(result[0])
        self.assertNotEqual(result[2], "N/A")  # Ballot hash
        self.assertNotEqual(result[3], "N/A")  # Signature hex

    def test_tampered_ballot_rejected(self):
        priv1, pub1 = generate_keys()
        priv2, pub2 = generate_keys()
        ballot = "100000000001|bjp|1600000000.0"

        # Using wrong public key should fail
        result = verify_vote(priv1, pub2, ballot)
        self.assertFalse(result[0])

    def test_corrupted_key_handling(self):
        result = verify_vote("invalid-pem-key", "invalid-pub-key", "ballot-content")
        self.assertFalse(result[0])

class VotingWorkflowTests(TestCase):
    """
    Tests authentication, OTP verification, vote creation, and duplicate prevention.
    """
    def setUp(self):
        self.client = Client()
        self.voter = Voters.objects.create(
            uuid="540399430308",
            name="Supreeth",
            dob=datetime.date(2005, 2, 2),
            pincode="506321",
            region="Hanamkonda",
            email="2303a51770@sru.edu.in",
            vote_done=False
        )
        self.party = PoliticalParty.objects.create(
            party_id="bjp",
            party_name="Bharatiya Janata Party",
            candidate_name="Narendra Modi",
            party_logo="/static/images/parties/bjp.svg"
        )
        MiningInfo.objects.create(id=0, prev_hash="0"*64, last_block_id="0")

    def test_voter_authentication(self):
        response = self.client.post('/authentication/', {'aadhar_no': '540399430308'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['details']['name'], 'Supreeth')

    def test_invalid_aadhar_authentication(self):
        response = self.client.post('/authentication/', {'aadhar_no': '999999999999'})
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('No voter found', data['error'])

    def test_otp_flow(self):
        session = self.client.session
        session['uuid'] = self.voter.uuid
        session.save()

        # Send OTP
        resp = self.client.post('/send-otp/', {'email-id': '2303a51770@sru.edu.in'})
        data = resp.json()
        self.assertTrue(data['success'])
        otp = data.get('otp')
        self.assertIsNotNone(otp)

        # Verify OTP
        resp_verify = self.client.post('/verify-otp/', {'otp-input': otp})
        self.assertTrue(resp_verify.json()['success'])

    def test_full_vote_creation_and_duplicate_prevention(self):
        # Authenticate
        self.client.post('/authentication/', {'aadhar_no': '540399430308'})

        # Verify OTP
        session = self.client.session
        session['uuid'] = self.voter.uuid
        session['email-verified'] = True
        session.save()

        # Get parties & keypair
        resp_parties = self.client.get('/get-parties/')
        parties_data = resp_parties.json()
        private_key = parties_data['private_key']

        # Cast vote
        resp_vote = self.client.post('/create-vote/', {
            'selected-party-id': 'bjp',
            'private-key': private_key
        })
        vote_data = resp_vote.json()
        self.assertTrue(vote_data['success'])

        # Verify database state
        voter_db = Voters.objects.get(uuid='540399430308')
        self.assertTrue(voter_db.vote_done)
        self.assertEqual(Vote.objects.filter(uuid='540399430308').count(), 1)
        self.assertEqual(VoteBackup.objects.filter(uuid='540399430308').count(), 1)

        # Attempt duplicate vote - should be rejected!
        resp_dup = self.client.post('/create-vote/', {
            'selected-party-id': 'bjp',
            'private-key': private_key
        })
        self.assertFalse(resp_dup.json()['success'])
        self.assertIn('Duplicate', resp_dup.json()['status'])

class BlockchainConsensusTests(TestCase):
    """
    Tests block mining, Proof-of-Work, tamper detection, and self-healing consensus.
    """
    def setUp(self):
        self.client = Client()
        MiningInfo.objects.create(id=0, prev_hash="0"*64, last_block_id="0")
        self.party = PoliticalParty.objects.create(
            party_id="bjp",
            party_name="BJP",
            candidate_name="Narendra Modi"
        )
        self.party2 = PoliticalParty.objects.create(
            party_id="congress",
            party_name="INC",
            candidate_name="Mallikarjun Kharge"
        )
        # Create 2 votes with identical timestamp
        t = timezone.now()
        Vote.objects.create(uuid="1001", vote_party_id="bjp", timestamp=t)
        VoteBackup.objects.create(uuid="1001", vote_party_id="bjp", timestamp=t)

    def test_mining_creates_valid_block(self):
        from .views import create_block
        data = create_block()
        self.assertEqual(len(data['result']), 1)
        block = Block.objects.get(id=1)
        self.assertEqual(block.prev_hash, "0"*64)
        self.assertTrue(block.this_hash.startswith(settings.PUZZLE))
        self.assertIsNotNone(block.nonce)

    def test_tamper_detection_and_sync_recovery(self):
        from .views import create_block
        create_block()

        # Initially intact
        resp = self.client.get('/verify-block/?selected[]=1')
        self.assertEqual(resp.json(), {"1": False})

        # Simulate cyberattack / tampering
        tamper_resp = self.client.get('/tamper-block/?block-id=1')
        self.assertTrue(tamper_resp.json()['success'])

        # Now detected as tampered
        resp_tampered = self.client.get('/verify-block/?selected[]=1')
        self.assertEqual(resp_tampered.json(), {"1": True})

        # Self-healing sync
        sync_resp = self.client.get('/sync-block/?block-id=1')
        self.assertTrue(sync_resp.json()['success'])

        # Verified intact again
        resp_restored = self.client.get('/verify-block/?selected[]=1')
        self.assertEqual(resp_restored.json(), {"1": False})

    def test_show_result_view(self):
        resp = self.client.get('/show-result/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "BJP")

    def test_sample_voters_api(self):
        Voters.objects.create(
            uuid="100000000001",
            name="Aarav Sharma",
            dob=datetime.date(1990, 1, 1),
            pincode="110001",
            region="Delhi",
            vote_done=False
        )
        resp = self.client.get('/api/sample-voters/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('unvoted', data)
        self.assertTrue(len(data['unvoted']) > 0)
