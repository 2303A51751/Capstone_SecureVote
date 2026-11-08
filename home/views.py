from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.forms.models import model_to_dict
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from .models import Voters, PoliticalParty, Vote, VoteBackup, Block, MiningInfo
from .methods_module import (
    send_email_otp,
    generate_keys,
    verify_vote,
    send_email_private_key,
    send_vote_confirmation_email,
    vote_count,
)

from Crypto.Hash import SHA3_256
from .merkle_tool import MerkleTools
import datetime
import json
import time
import random
import string

ts_data = {
    'progress': False,
    'status': 'System Ready',
    'completed': 0
}

# ----------------- Helper: Ensure Genesis Mining State -----------------
def get_or_create_mining_info():
    """
    Ensures that the Genesis mining info record exists.
    """
    info = MiningInfo.objects.first()
    if not info:
        info = MiningInfo.objects.create(
            id=0,
            prev_hash='0' * 64,
            last_block_id='0'
        )
    return info

# -------------- Home (First time loading) --------------
@ensure_csrf_cookie
def home(request):
    return render(request, 'home.html')

# --------------- Authentication -------------------
@csrf_exempt
def authentication(request):
    """
    Authenticates a voter using their Aadhaar / UIDAI number.
    Handles both POST and GET for robust frontend compatibility.
    """
    aadhar_no = request.POST.get('aadhar_no') or request.GET.get('aadhar_no')
    if aadhar_no:
        aadhar_no = aadhar_no.strip().replace(' ', '').replace('-', '')

    details = {'success': False}

    if not aadhar_no:
        details['error'] = 'Please enter a valid Aadhaar number.'
        return JsonResponse(details)

    try:
        # Check direct match
        voter = Voters.objects.filter(uuid=aadhar_no).first()

        # Fallback: if user typed short numeric id (e.g. "7" instead of "100000000007" or vice versa)
        if not voter and aadhar_no.isdigit():
            padded = f"1000000000{int(aadhar_no):02d}"
            voter = Voters.objects.filter(uuid=padded).first()
            if not voter:
                voter = Voters.objects.filter(uuid=str(int(aadhar_no))).first()

        if not voter:
            details['error'] = f'No voter found matching Aadhaar "{aadhar_no}". Please check the number or use a demo voter below.'
            return JsonResponse(details)

        request.session['uuid'] = voter.uuid
        render_html = loader.render_to_string('candidate_details.html', {'details': voter}, request=request)

        if voter.vote_done:
            details = {
                'success': False,
                'error': f'Voter {voter.name} ({voter.uuid}) has already casted their vote! Duplicate voting is prevented by the blockchain system.',
                'already_voted': True,
                'voter_name': voter.name,
                'voter_uuid': voter.uuid
            }
        else:
            details = {
                'success': True,
                'html': render_html,
                'details': model_to_dict(voter)
            }
    except Exception as e:
        details = {
            'error': f'Authentication failed: {str(e)}'
        }

    return JsonResponse(details)

# --------- Reset voter vote status (Demo Helper) -----------
@csrf_exempt
def reset_voter(request):
    """
    Demo Helper: Resets a voter's vote status to False so users can test voting repeatedly.
    """
    uuid = request.POST.get('uuid') or request.GET.get('uuid')
    if uuid:
        uuid = uuid.strip().replace(' ', '').replace('-', '')
        voter = Voters.objects.filter(uuid=uuid).first()
        if not voter and uuid.isdigit():
            padded = f"1000000000{int(uuid):02d}"
            voter = Voters.objects.filter(uuid=padded).first()

        if voter:
            voter.vote_done = False
            voter.save()
            # Also clean up unsealed vote if any
            Vote.objects.filter(uuid=voter.uuid, block_id=None).delete()
            VoteBackup.objects.filter(uuid=voter.uuid, block_id=None).delete()
            return JsonResponse({'success': True, 'message': f'Voter {voter.name} is now reset and ready to vote!'})
    return JsonResponse({'success': False, 'error': 'Voter not found'})

# --------- Send otp for email verification -----------
@csrf_exempt
def send_otp(request):
    """
    Generates and sends an OTP strictly to the voter's registered email address.
    In Demo Mode, outputs OTP in response/console for seamless offline testing.
    """
    uuid = request.session.get('uuid')
    email_input = None
    if uuid:
        voter = Voters.objects.filter(uuid=uuid).first()
        if voter and voter.email:
            email_input = voter.email

    if not email_input:
        email_input = request.POST.get('email-id') or request.GET.get('email-id')
        if email_input:
            email_input = email_input.strip()

    if not email_input:
        return JsonResponse({'success': False, 'error': 'No registered email found for this voter.'})

    otp_res = send_email_otp(email_input)
    success = otp_res[0]
    otp_code = otp_res[1]
    is_demo = otp_res[2] if len(otp_res) > 2 else False

    res = {'success': success}
    if success:
        request.session['otp'] = str(otp_code)
        request.session['email-id'] = email_input
        request.session['email-verified'] = False
        res['email'] = email_input
        res['demo_mode'] = is_demo
        if is_demo:
            res['otp'] = str(otp_code)
            res['message'] = f'[Demo Mode] OTP is: {otp_code} (Auto-filled). Configure EMAIL_ADDRESS in .env for live inbox delivery.'
        else:
            res['message'] = f'OTP sent successfully to your registered inbox: {email_input}. Please check your email.'
    else:
        res['error'] = str(otp_code)

    return JsonResponse(res)

# -------- Verify email with provided otp ----------
@csrf_exempt
def verify_otp(request):
    """
    Verifies the OTP submitted by the voter.
    """
    otp_input = request.POST.get('otp-input') or request.GET.get('otp-input')
    if otp_input:
        otp_input = otp_input.strip()

    expected_otp = str(request.session.get('otp', '')).strip()

    res = {'success': False}
    if otp_input and expected_otp and otp_input == expected_otp:
        uuid = request.session.get('uuid')
        if uuid:
            voter = Voters.objects.filter(uuid=uuid).first()
            if voter:
                voter.email = request.session.get('email-id', '')
                voter.save()
        res['success'] = True
        request.session['email-verified'] = True
    else:
        res['error'] = 'Invalid OTP. Please enter the correct verification code.'

    return JsonResponse(res)

# --------- On successful email verification show all parties options ----------
@csrf_exempt
def get_parties(request):
    """
    Generates an ECC key pair for the voter, stores public key in session,
    sends private key, and renders the voting ballot page.
    """
    party_list = {}
    if request.session.get('email-verified'):
        private_key, public_key = generate_keys()

        # Store keys in session
        request.session['public-key'] = public_key
        request.session['private-key'] = private_key

        email_id = request.session.get('email-id', 'demo@voter.org')
        send_email_private_key(email_id, private_key)

        parties = list(PoliticalParty.objects.all())
        parties_dict = [model_to_dict(party) for party in parties]

        render_html = loader.render_to_string('voting.html', {'parties': parties_dict}, request=request)

        party_list = {
            'html': render_html,
            'parties': parties_dict,
            'private_key': private_key  # Returned for UI quick-paste / demo helper
        }
    else:
        party_list = {'error': 'Email not verified. Please complete OTP verification first.'}

    return JsonResponse(party_list)

# ------------- Save vote in database ------------------------
@csrf_exempt
def create_vote(request):
    """
    Receives ballot selection and voter's ECDSA private key.
    Digitally signs ballot with SHA3-256 and verifies the DSS signature.
    Prevents duplicate votes, stores in database & backup ledger,
    and dispatches real-time confirmation receipt to registered email.
    """
    uuid = request.session.get('uuid')
    if not uuid:
        return JsonResponse({'success': False, 'status': 'Session expired. Please authenticate again.'})

    private_key = request.POST.get('private-key') or request.GET.get('private-key')
    selected_party_id = request.POST.get('selected-party-id') or request.GET.get('selected-party-id')
    public_key = request.session.get('public-key')

    voter = Voters.objects.filter(uuid=uuid).first()
    email_to = voter.email if voter else request.session.get('email-id')
    voter_name = voter.name if voter else "Voter"

    if not private_key:
        if email_to:
            send_vote_confirmation_email(
                email_to, voter_name, uuid, False,
                failure_reason='Cryptographic Private Key was missing.'
            )
        return JsonResponse({'success': False, 'status': 'Cryptographic Private Key is required to digitally sign your vote.'})

    if not selected_party_id:
        if email_to:
            send_vote_confirmation_email(
                email_to, voter_name, uuid, False,
                failure_reason='No candidate or political party was selected.'
            )
        return JsonResponse({'success': False, 'status': 'Please select a candidate/party.'})

    if not public_key:
        if email_to:
            send_vote_confirmation_email(
                email_to, voter_name, uuid, False,
                failure_reason='Public key missing from session. Please re-authenticate.'
            )
        return JsonResponse({'success': False, 'status': 'Public key missing from session. Please re-authenticate.'})

    # Check duplicate vote
    if voter and voter.vote_done:
        if email_to:
            send_vote_confirmation_email(
                email_to, voter_name, uuid, False,
                failure_reason='Duplicate vote attempt rejected. This citizen ID has already cast a ballot.'
            )
        return JsonResponse({'success': False, 'status': 'Duplicate vote rejected! You have already casted your vote.'})

    curr = timezone.now()
    ballot = f'{uuid}|{selected_party_id}|{curr.timestamp()}'

    status = verify_vote(private_key, public_key, ballot)
    context = {'success': status[0], 'status': status[1]}

    party = PoliticalParty.objects.filter(party_id=selected_party_id).first()
    party_name = party.party_name if party else selected_party_id
    candidate_name = party.candidate_name if (party and party.candidate_name) else "Official Candidate"

    if status[0]:
        try:
            Vote.objects.create(uuid=uuid, vote_party_id=selected_party_id, timestamp=curr)
            VoteBackup.objects.create(uuid=uuid, vote_party_id=selected_party_id, timestamp=curr)
            if voter:
                voter.vote_done = True
                voter.save()
            context['status'] = 'Vote verified and digitally signed successfully! Stored in mempool awaiting block sealing.'

            # Dispatch Real-Time Official Confirmation Receipt to Voter's Inbox!
            if email_to:
                send_vote_confirmation_email(
                    email_to=email_to,
                    voter_name=voter_name,
                    aadhaar=uuid,
                    is_success=True,
                    party_name=party_name,
                    candidate_name=candidate_name,
                    timestamp_str=curr.strftime('%d %B %Y, %I:%M:%S %p UTC'),
                    ballot_hash=status[2],
                    signature_hex=status[3]
                )

        except Exception as e:
            context['success'] = False
            context['status'] = f'Unable to store vote in blockchain mempool: {str(e)}'
            if email_to:
                send_vote_confirmation_email(
                    email_to=email_to,
                    voter_name=voter_name,
                    aadhaar=uuid,
                    is_success=False,
                    failure_reason=f'Database storage error: {str(e)}'
                )
    else:
        # Digital signature verification failed
        if email_to:
            send_vote_confirmation_email(
                email_to=email_to,
                voter_name=voter_name,
                aadhaar=uuid,
                is_success=False,
                failure_reason=f'Cryptographic digital signature verification failed: {status[1]}'
            )

    html = loader.render_to_string('final-status.html', {
        'ballot': status[2],
        'ballot_signature': status[3],
        'status': context['status'],
        'email': email_to,
        'voter_name': voter_name,
        'party_name': party_name,
        'is_success': context['success']
    }, request=request)
    context['html'] = html

    return JsonResponse(context)

# -------------- create Dummy Data ------------------
@csrf_exempt
def create_dummy_data(request):
    to_do = {
        'createRandomVoters': json.loads(request.GET.get('createRandomVoters', 'null')) if request.GET.get('createRandomVoters') else None,
        'createPoliticianParties': json.loads(request.GET.get('createPoliticianParties', 'null')) if request.GET.get('createPoliticianParties') else None,
        'castRandomVote': json.loads(request.GET.get('castRandomVote', 'null')) if request.GET.get('castRandomVote') else None,
    }
    if to_do['createRandomVoters'] is not None or to_do['createPoliticianParties'] is not None or to_do['castRandomVote'] is not None:
        dummy_data_input(to_do)
        return JsonResponse({'success': True})
    return render(request, 'create-dummy-data.html')

# -------------- Show Vote count so far -----------
def show_result(request):
    vote_result = vote_count()
    vote_result = dict(reversed(sorted(vote_result.items(), key=lambda vr: (vr[1], vr[0]))))
    results = []
    political_parties = PoliticalParty.objects.all()
    total_votes = Vote.objects.count()

    i = 0
    winner = None
    max_votes = -1

    for party_id, votecount in vote_result.items():
        i += 1
        try:
            party = political_parties.get(party_id=party_id)
            party_name = party.party_name
            party_logo = party.party_logo
            candidate_name = party.candidate_name
        except PoliticalParty.DoesNotExist:
            party_name = party_id.upper()
            party_logo = '/static/images/logo.png'
            candidate_name = 'Candidate'

        percentage = round((votecount / total_votes * 100), 1) if total_votes > 0 else 0

        if votecount > max_votes and votecount > 0:
            max_votes = votecount
            winner = party_name

        results.append({
            'sr': i,
            'party_id': party_id,
            'party_name': party_name,
            'party_symbol': party_logo,
            'candidate_name': candidate_name,
            'vote_count': votecount,
            'percentage': percentage,
        })

    sealed_votes = Vote.objects.exclude(block_id=None).count()
    unsealed_votes = Vote.objects.filter(block_id=None).count()
    total_blocks = Block.objects.count()

    context = {
        'results': results,
        'total_votes': total_votes,
        'sealed_votes': sealed_votes,
        'unsealed_votes': unsealed_votes,
        'total_blocks': total_blocks,
        'winner': winner,
    }
    return render(request, 'show-result.html', context)

# ------------- Show Block Mining Page -------------
def mine_block(request):
    to_seal_votes_count = Vote.objects.filter(block_id=None).count()
    total_blocks = Block.objects.count()
    return render(request, 'mine-block.html', {
        'data': to_seal_votes_count,
        'total_blocks': total_blocks,
        'puzzle': settings.PUZZLE,
    })

# ----------------- Start mining on button click ---------------
@csrf_exempt
def start_mining(request):
    data = create_block()
    html = loader.render_to_string('mined-blocks.html', data, request=request)
    return JsonResponse({'html': html, 'mined_count': len(data.get('result', []))})

# Create block [called in start_mining()]
def create_block():
    mining_info = get_or_create_mining_info()
    prev_hash = mining_info.prev_hash
    curr_block_id = int(mining_info.last_block_id or 0)
    last_block_id = curr_block_id

    # Transactions ordered chronologically (ascending)
    non_sealed_votes = list(Vote.objects.filter(block_id=None).order_by('timestamp'))
    non_sealed_votes_BACKUP = list(VoteBackup.objects.filter(block_id=None).order_by('timestamp'))

    txn_per_block = max(1, getattr(settings, 'TRANSACTIONS_PER_BLOCK', 1))
    number_of_blocks = int(len(non_sealed_votes) / txn_per_block)

    puzzle = getattr(settings, 'PUZZLE', '000')
    pcount = len(puzzle)

    time_start = time.time()
    result = []

    ts_data['progress'] = True
    ts_data['status'] = 'Mining has been Initialized.'
    ts_data['completed'] = 0

    if number_of_blocks == 0:
        ts_data['progress'] = False
        ts_data['status'] = 'No pending transactions to seal.'
        return {'time_taken': 0.0, 'result': []}

    for idx in range(number_of_blocks):
        start_idx = idx * txn_per_block
        end_idx = start_idx + txn_per_block
        block_transactions = non_sealed_votes[start_idx:end_idx]
        block_transactions_BACKUP = non_sealed_votes_BACKUP[start_idx:end_idx]

        # Merkle Tree calculation with SHA3-256
        root = MerkleTools()
        leaves = [f'{tx.uuid}|{tx.vote_party_id}|{tx.timestamp}' for tx in block_transactions]
        root.add_leaf(leaves, True)
        root.make_tree()
        merkle_h = root.get_merkle_root() or ('0' * 64)

        # Proof-of-Work: Find nonce meeting target difficulty
        nonce = 0
        timestamp = timezone.now()
        while True:
            enc = f'{prev_hash}{merkle_h}{nonce}{timestamp.timestamp()}'.encode('utf-8')
            h = SHA3_256.new(enc).hexdigest()
            if h[:pcount] == puzzle:
                break
            nonce += 1

        # Create Block record
        curr_block_id += 1
        Block.objects.create(
            id=curr_block_id,
            prev_hash=prev_hash,
            merkle_hash=merkle_h,
            this_hash=h,
            nonce=nonce,
            timestamp=timestamp
        )

        result.append({
            'block_id': curr_block_id,
            'prev_hash': prev_hash,
            'merkle_hash': merkle_h,
            'this_hash': h,
            'nonce': nonce,
            'tx_count': len(block_transactions)
        })

        # Set this block's hash as next block's prev_hash
        prev_hash = h

        # Mark transactions as sealed with block_id
        for txn in block_transactions:
            txn.block_id = str(curr_block_id)
            txn.save()
        for txn in block_transactions_BACKUP:
            txn.block_id = str(curr_block_id)
            txn.save()

        blocks_mined = curr_block_id - last_block_id
        ts_data['status'] = f'{blocks_mined} blocks mined. ({blocks_mined * txn_per_block} votes sealed into blockchain ledger.)'
        ts_data['completed'] = round((idx + 1) * 100 / number_of_blocks)

    time_end = time.time()
    time_taken = max(0.000001, time_end - time_start)

    # Save current Mining info
    mining_info.prev_hash = prev_hash
    mining_info.last_block_id = str(curr_block_id)
    mining_info.save()

    data = {
        'time_taken': round(time_taken, 4),
        'result': result
    }

    ts_data['progress'] = False
    return data

def dummy_data_input(to_do):
    """
    Seeds realistic Indian election data: parties, candidates, and citizens.
    Leaves sample unvoted citizens so live voting can be demonstrated immediately!
    """
    ts_data['progress'] = True
    ts_data['status'] = 'Resetting previous data.'
    ts_data['completed'] = 10

    PoliticalParty.objects.all().delete()
    Voters.objects.all().delete()
    Vote.objects.all().delete()
    Block.objects.all().delete()
    VoteBackup.objects.all().delete()
    MiningInfo.objects.all().delete()

    MiningInfo.objects.create(id=0, prev_hash='0' * 64, last_block_id='0')

    ts_data['completed'] = 30

    parties = {
        'bjp': {
            'party_id': 'bjp',
            'party_name': 'Bharatiya Janata Party (BJP)',
            'party_logo': '/static/images/parties/bjp.svg',
            'candidate_name': 'Narendra Modi',
            'candidate_profile_pic': '/static/images/parties/bjp.svg'
        },
        'congress': {
            'party_id': 'congress',
            'party_name': 'Indian National Congress (INC)',
            'party_logo': '/static/images/parties/congress.svg',
            'candidate_name': 'Mallikarjun Kharge',
            'candidate_profile_pic': '/static/images/parties/congress.svg'
        },
        'aap': {
            'party_id': 'aap',
            'party_name': 'Aam Aadmi Party (AAP)',
            'party_logo': '/static/images/parties/aap.svg',
            'candidate_name': 'Arvind Kejriwal',
            'candidate_profile_pic': '/static/images/parties/aap.svg'
        },
        'bsp': {
            'party_id': 'bsp',
            'party_name': 'Bahujan Samaj Party (BSP)',
            'party_logo': '/static/images/parties/bsp.svg',
            'candidate_name': 'Mayawati',
            'candidate_profile_pic': '/static/images/parties/bsp.svg'
        },
        'nota': {
            'party_id': 'nota',
            'party_name': 'None of the Above (NOTA)',
            'party_logo': '/static/images/parties/nota.svg',
            'candidate_name': 'None of the Above',
            'candidate_profile_pic': '/static/images/parties/nota.svg'
        }
    }

    if to_do.get('createPoliticianParties'):
        ts_data['status'] = 'Creating national political parties...'
        for p in parties.values():
            PoliticalParty.objects.create(
                party_id=p['party_id'],
                party_name=p['party_name'],
                party_logo=p['party_logo'],
                candidate_name=p['candidate_name'],
                candidate_profile_pic=p['candidate_profile_pic']
            )

    ts_data['completed'] = 60

    # Project Team Members (Official Electoral Roll)
    sample_voters = [
        {
            'uuid': '540399430308',
            'name': 'Supreeth',
            'dob': datetime.date(2005, 2, 2),
            'pincode': '506321',
            'region': 'Hanamkonda',
            'email': '2303a51770@sru.edu.in'
        },
        {
            'uuid': '319793558085',
            'name': 'Abhishek',
            'dob': datetime.date(2004, 3, 3),
            'pincode': '506371',
            'region': 'Hanamkonda',
            'email': '2303a51762@sru.edu.in'
        },
        {
            'uuid': '416710509637',
            'name': 'Awez ali',
            'dob': datetime.date(2006, 4, 4),
            'pincode': '506371',
            'region': 'Hanamkonda',
            'email': '2303a51767@sru.edu.in'
        },
        {
            'uuid': '652196177770',
            'name': 'Charith',
            'dob': datetime.date(2006, 4, 26),
            'pincode': '503321',
            'region': 'Nizamabad',
            'email': '2303a51751@sru.edu.in'
        },
    ]

    if to_do.get('createRandomVoters'):
        ts_data['status'] = 'Registering verified team members on electoral roll...'
        for v in sample_voters:
            Voters.objects.create(
                uuid=v['uuid'],
                name=v['name'],
                dob=v['dob'],
                pincode=v['pincode'],
                region=v['region'],
                email=v['email'],
                profile_pic='/static/images/profile-bg.png',
                vote_done=False
            )

    ts_data['completed'] = 80

    # Team members start unvoted so they can cast their votes live
    ts_data['status'] = 'Electoral database initialized with team members!'
    ts_data['completed'] = 100
    ts_data['progress'] = False

def blockchain(request):
    """
    Renders the public blockchain explorer table.
    """
    blocks = Block.objects.all().order_by('id')
    total_blocks = blocks.count()
    total_votes = Vote.objects.count()
    sealed_votes = Vote.objects.exclude(block_id=None).count()
    pending_votes = Vote.objects.filter(block_id=None).count()

    context = {
        'blocks': blocks,
        'total_blocks': total_blocks,
        'total_votes': total_votes,
        'sealed_votes': sealed_votes,
        'pending_votes': pending_votes,
    }
    return render(request, 'blockchain.html', context)

def block_info(request):
    """
    Displays full cryptographic details of a single block.
    Recalculates Merkle Root from database transactions to detect tampering.
    """
    block_id = request.GET.get('id') or request.POST.get('id')
    try:
        block = Block.objects.get(id=block_id)
        confirmed_by = (Block.objects.count() - block.id) + 1

        # Ordering MUST match create_block (ascending timestamp)
        votes = list(Vote.objects.filter(block_id=block_id).order_by('timestamp'))

        vote_hashes = [
            SHA3_256.new(f'{vote.uuid}|{vote.vote_party_id}|{vote.timestamp}'.encode('utf-8')).hexdigest()
            for vote in votes
        ]

        root = MerkleTools()
        if votes:
            root.add_leaf([f'{vote.uuid}|{vote.vote_party_id}|{vote.timestamp}' for vote in votes], True)
            root.make_tree()
            merkle_hash = root.get_merkle_root() or ('0' * 64)
        else:
            merkle_hash = '0' * 64

        tampered = (block.merkle_hash != merkle_hash)

        context = {
            'this_block': block,
            'confirmed_by': confirmed_by,
            'votes': zip(votes, vote_hashes),
            'vote_count': len(votes),
            're_merkle_hash': merkle_hash,
            'isTampered': tampered,
        }
        return render(request, 'block-info.html', context)
    except Exception as e:
        print(f"block_info error: {e}")
        return render(request, 'block-info.html', {'error': f'Block {block_id} not found: {str(e)}'})

@csrf_exempt
def sync_block(request):
    """
    Self-Healing Consensus Recovery:
    Restores tampered vote transactions in a block from immutable consensus backup.
    """
    block_id = request.GET.get('block-id') or request.POST.get('block-id')
    try:
        backup_votes = VoteBackup.objects.filter(block_id=block_id).order_by('timestamp')
        if not backup_votes.exists():
            return JsonResponse({'success': False, 'error': f'No backup records for block {block_id}'})

        for vote in backup_votes:
            x_vote, created = Vote.objects.get_or_create(uuid=vote.uuid, defaults={
                'vote_party_id': vote.vote_party_id,
                'timestamp': vote.timestamp,
                'block_id': vote.block_id
            })
            if not created:
                x_vote.vote_party_id = vote.vote_party_id
                x_vote.timestamp = vote.timestamp
                x_vote.block_id = vote.block_id
                x_vote.save()

        return JsonResponse({'success': True, 'message': f'Block #{block_id} restored and re-synchronized from consensus ledger.'})
    except Exception as e:
        print(f"sync_block error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def tamper_block(request):
    """
    DEMO / VIVA FEATURE:
    Simulates a cyberattack by intentionally corrupting a vote transaction in the database.
    This alters the Merkle Tree, proving to examiners that the blockchain detects tampering.
    """
    block_id = request.GET.get('block-id') or request.POST.get('block-id')
    try:
        votes = Vote.objects.filter(block_id=block_id).order_by('timestamp')
        if not votes.exists():
            return JsonResponse({'success': False, 'error': f'No votes in block {block_id} to tamper.'})

        target_vote = votes.first()
        original_party = target_vote.vote_party_id
        # Swap to a different party
        new_party = 'nota' if original_party != 'nota' else 'bjp'
        target_vote.vote_party_id = new_party
        target_vote.save()

        return JsonResponse({
            'success': True,
            'message': f'Simulated Attack: Altered vote {target_vote.uuid} from "{original_party}" to "{new_party}". Merkle root hash is now invalidated!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def verify_block(request):
    """
    Verifies Merkle root hashes for a list of block IDs.
    """
    selected = request.GET.getlist('selected[]') or request.POST.getlist('selected[]')
    context = {}
    for s_block in selected:
        try:
            block = Block.objects.get(id=s_block)
            votes = Vote.objects.filter(block_id=s_block).order_by('timestamp')

            root = MerkleTools()
            if votes.exists():
                root.add_leaf([f'{vote.uuid}|{vote.vote_party_id}|{vote.timestamp}' for vote in votes], True)
                root.make_tree()
                merkle_hash = root.get_merkle_root() or ('0' * 64)
            else:
                merkle_hash = '0' * 64

            tampered = (block.merkle_hash != merkle_hash)
            context[s_block] = tampered
        except Block.DoesNotExist:
            context[s_block] = True

    return JsonResponse(context)

def get_sample_voters(request):
    """
    API endpoint returning sample ready-to-vote and already-voted citizens
    for instant one-click testing on the homepage.
    """
    unvoted = list(Voters.objects.filter(vote_done=False).values('uuid', 'name', 'region', 'email'))
    voted = list(Voters.objects.filter(vote_done=True).values('uuid', 'name', 'region', 'email'))
    return JsonResponse({
        'unvoted': unvoted,
        'voted': voted,
        'total_voters': Voters.objects.count()
    })

def track_server(request):
    return JsonResponse(ts_data)
