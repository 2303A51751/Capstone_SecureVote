import smtplib
from email.message import EmailMessage
from django.conf import settings
from django.utils import timezone
import random
import string
import logging

from .models import PoliticalParty, Vote
from Crypto.Hash import SHA3_256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS

logger = logging.getLogger(__name__)

def _dispatch_smtp_message(email_address, email_password, msg):
    """
    Attempts delivery first on configured port, falling back to alternate port (465 SSL <-> 587 TLS)
    to bypass restrictive local Wi-Fi/firewall blocks. Automatically strips whitespace and spaces
    from Google 16-character App Passwords.
    """
    host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com').strip()
    preferred_port = int(getattr(settings, 'EMAIL_PORT', 465))
    clean_password = email_password.strip().replace(' ', '')
    clean_address = email_address.strip()

    ports = [preferred_port, 587 if preferred_port == 465 else 465]
    last_err = None

    for port in ports:
        try:
            if port == 465:
                smtp = smtplib.SMTP_SSL(host, port, timeout=12)
            else:
                smtp = smtplib.SMTP(host, port, timeout=12)
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
            smtp.login(clean_address, clean_password)
            smtp.send_message(msg)
            smtp.quit()
            return True, None
        except Exception as e:
            last_err = e
            continue

    return False, last_err

def send_email_otp(email_to):
    """
    Sends an OTP to the given email address.
    If SMTP credentials are configured, sends via SMTP to the registered SRU email inbox.
    If SMTP is not yet configured or connection fails, falls back gracefully to demo output.
    """
    # Generate 6-digit numeric OTP
    otp = ''.join(random.choice(string.digits) for _ in range(6))
    
    email_address = getattr(settings, 'EMAIL_ADDRESS', '').strip()
    email_password = getattr(settings, 'EMAIL_PASSWORD', '').strip()

    if not email_address or not email_password:
        print(f"\n{'='*65}\n[DEMO MODE: OTP GENERATED FOR REGISTERED EMAIL: {email_to}]")
        print(f"OTP Code: {otp}")
        print(f"To receive real-time emails in inboxes, configure EMAIL_ADDRESS & EMAIL_PASSWORD in .env")
        print(f"{'='*65}\n")
        return [True, otp, True]

    msg = EmailMessage()
    msg['From'] = f"SRU E-Voting Portal <{email_address}>"
    msg['To'] = email_to
    msg['Subject'] = 'SRU Blockchain E-Voting - One-Time Passcode (OTP)'
    content = (
        f"Dear Voter,\n\n"
        f"Your One-Time Passcode (OTP) to authenticate your identity on the Blockchain E-Voting System is: {otp}\n\n"
        f"This OTP is valid for your current voting session.\n\n"
        f"Thank you.\nSRU Blockchain Electoral Commission"
    )
    msg.set_content(content)
    msg.add_alternative(f'''\
        <!DOCTYPE html>
        <html>
            <body style="font-family: Arial, sans-serif; padding: 25px; color: #333; max-width: 550px; margin: auto; border: 1px solid #e5e7eb; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #7e22ce, #4c1d95); padding: 15px; border-radius: 8px; text-align: center; color: white;">
                    <h2 style="margin: 0;">SRU Blockchain E-Voting System</h2>
                    <span style="font-size: 12px; opacity: 0.9;">Secure • Decentralized • Auditable</span>
                </div>
                <div style="padding: 20px 0;">
                    <p>Hello,</p>
                    <p>You have initiated an official voter authentication session. Your One-Time Passcode (OTP) to issue your <strong>NIST P-256 ECDSA Cryptographic Private Key</strong> is:</p>
                    <div style="background: #faf5ff; border: 2px dashed #c084fc; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                        <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #6b21a8;">{otp}</span>
                    </div>
                    <p style="font-size: 13px; color: #666;">This passcode is intended strictly for: <strong>{email_to}</strong>.</p>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 11px; color: #999; text-align: center;">SR University • Blockchain Electoral Network</p>
            </body>
        </html>
    ''', subtype='html')

    ok, err = _dispatch_smtp_message(email_address, email_password, msg)
    if ok:
        print(f"\n[REAL-TIME OTP DELIVERED] Successfully delivered OTP to inbox: {email_to}\n")
        return [True, otp, False]
    else:
        err_str = str(err)
        if '535' in err_str or 'BadCredentials' in err_str or 'Username and Password not accepted' in err_str:
            print("\n" + "!"*65)
            print("[GOOGLE SMTP AUTHENTICATION ERROR 535]")
            print("Google rejected the password because Google requires a 16-character 'App Password'.")
            print("Normal account passwords do not work with Gmail SMTP.")
            print("Steps to fix:")
            print("  1. Go to: https://myaccount.google.com/apppasswords")
            print("  2. Create an App Password for 'Mail' / 'Django Voting'")
            print("  3. Copy the 16-character code (e.g. abcd efgh ijkl mnop)")
            print("  4. Paste it into EMAIL_PASSWORD in your .env file")
            print("!"*65 + "\n")
        logger.warning(f"SMTP delivery to {email_to} failed: {err}. Falling back to demo mode.")
        print(f"\n[SMTP FAILED: {err}]\nFalling back to Demo Mode. Generated OTP for {email_to}: {otp}\n")
        return [True, otp, True]

def send_email_private_key(email_to, private_key):
    """
    Sends the generated ECDSA private key to the voter's registered email address.
    """
    print(f"\n{'='*65}\n[ECDSA PRIVATE KEY ISSUED FOR {email_to}]\n{private_key}\n{'='*65}\n")
    
    email_address = getattr(settings, 'EMAIL_ADDRESS', '').strip()
    email_password = getattr(settings, 'EMAIL_PASSWORD', '').strip()

    if not email_address or not email_password:
        return [True]

    msg = EmailMessage()
    msg['From'] = f"SRU E-Voting Portal <{email_address}>"
    msg['To'] = email_to
    msg['Subject'] = 'Blockchain E-Voting - Your ECDSA Cryptographic Private Key'
    content = (
        f"Dear Voter,\n\n"
        f"Your NIST P-256 ECDSA Cryptographic Private Key for digitally signing your ballot has been generated:\n\n"
        f"{private_key}\n\n"
        f"Paste this key into the voting portal to authenticate your vote.\n\n"
        f"Thank you.\nSRU Blockchain Electoral Commission"
    )
    msg.set_content(content)

    ok, err = _dispatch_smtp_message(email_address, email_password, msg)
    if ok:
        print(f"[REAL-TIME EMAIL DELIVERED] Private key sent to inbox: {email_to}")
    else:
        logger.warning(f"SMTP private key send failed: {err}")
    return [True]

def generate_keys():
    """
    Generates an ECC key pair using the NIST P-256 (secp256r1) elliptic curve.
    Returns (private_key_pem, public_key_pem).
    """
    key = ECC.generate(curve='P-256')
    private_key = key.export_key(format='PEM')
    public_key = key.public_key().export_key(format='PEM')
    return private_key, public_key

def verify_vote(private_key, public_key, ballot):
    """
    Digitally signs a ballot with the voter's private key and verifies the signature
    with the corresponding public key using ECDSA (FIPS 186-3) with SHA3-256.
    """
    try:
        if not private_key or not public_key:
            return [False, 'Private key or public key missing.', 'N/A', 'N/A']

        # Import keys
        priv = ECC.import_key(private_key.strip())
        pub = ECC.import_key(public_key.strip())

        signer = DSS.new(priv, 'fips-186-3')
        verifier = DSS.new(pub, 'fips-186-3')

        ballot_hash = SHA3_256.new(ballot.encode('utf-8'))
        ballot_signature = signer.sign(ballot_hash)

        verifier.verify(ballot_hash, ballot_signature)
        return [
            True,
            'Your vote was cryptographically verified and ballot signed successfully.',
            ballot_hash.hexdigest(),
            ballot_signature.hex()
        ]
    except ValueError as e:
        return [False, f'Cryptographic key error: {str(e)}', 'N/A', 'N/A']
    except Exception as e:
        return [False, f'Digital signature verification failed: {str(e)}', 'N/A', 'N/A']

def vote_count():
    """
    Tallies votes grouped by political party.
    """
    parties_id = PoliticalParty.objects.values_list('party_id', flat=True)
    votes = Vote.objects.all()
    vote_result = {party: votes.filter(vote_party_id=party).count() for party in parties_id}
    return vote_result

def send_vote_confirmation_email(email_to, voter_name, aadhaar, is_success, **kwargs):
    """
    Sends an official Cryptographic Vote Receipt or Rejection Notice
    directly to the voter's registered university email inbox.
    """
    if not email_to:
        return [False, "No recipient email provided."]

    email_address = getattr(settings, 'EMAIL_ADDRESS', '').strip()
    email_password = getattr(settings, 'EMAIL_PASSWORD', '').strip()

    masked_aadhaar = f"XXXX-XXXX-{str(aadhaar)[-4:]}" if len(str(aadhaar)) >= 4 else str(aadhaar)
    timestamp_str = kwargs.get('timestamp_str') or timezone.now().strftime('%d %B %Y, %I:%M:%S %p UTC')
    party_name = kwargs.get('party_name', 'NOTA / Independent')
    candidate_name = kwargs.get('candidate_name', 'N/A')
    ballot_hash = kwargs.get('ballot_hash', 'N/A')
    signature_hex = kwargs.get('signature_hex', 'N/A')
    failure_reason = kwargs.get('failure_reason', 'Cryptographic verification or duplicate rejection')

    if is_success:
        subject = "🗳️ Vote Successfully Cast & Recorded - SRU Blockchain E-Voting"
        status_color = "#16a34a"
        status_badge = "CONFIRMED & SEALED"
        status_heading = "Your Vote Has Been Successfully Cast & Recorded!"
        status_msg = (
            f"Dear <strong>{voter_name}</strong>,<br><br>"
            f"Congratulations! Your ballot has been authenticated, cryptographically signed using your "
            f"<strong>NIST P-256 ECDSA Private Key</strong>, and permanently recorded in the "
            f"<strong>SRU Blockchain Transaction Pool (Mempool)</strong> awaiting block sealing."
        )
    else:
        subject = "⚠️ Vote Submission Alert - SRU Blockchain E-Voting"
        status_color = "#dc2626"
        status_badge = "REJECTED / FAILED"
        status_heading = "Vote Submission Notice: Action Could Not Be Completed"
        status_msg = (
            f"Dear <strong>{voter_name}</strong>,<br><br>"
            f"An attempt to cast a ballot associated with your registered citizen record "
            f"(Aadhaar: {masked_aadhaar}) could not be completed.<br><br>"
            f"<strong>Reason:</strong> <span style='color: #dc2626;'>{failure_reason}</span>"
        )

    # Console output for testing
    print(f"\n{'='*65}\n[VOTE CONFIRMATION EMAIL FOR {email_to}]\nSubject: {subject}\nStatus: {status_badge}\n{'='*65}\n")

    if not email_address or not email_password:
        return [True, "Demo Mode: Email logged to console."]

    msg = EmailMessage()
    msg['From'] = f"SRU Blockchain Electoral Commission <{email_address}>"
    msg['To'] = email_to
    msg['Subject'] = subject

    plain_content = (
        f"Dear {voter_name},\n\n"
        f"{'Your vote has been successfully cast and recorded!' if is_success else 'Your vote could not be recorded.'}\n\n"
        f"--- OFFICIAL BALLOT DETAILS ---\n"
        f"Voter: {voter_name} ({masked_aadhaar})\n"
        f"Timestamp: {timestamp_str}\n"
        + (f"Candidate / Party: {candidate_name} ({party_name})\n"
           f"SHA3-256 Ballot Hash: {ballot_hash}\n"
           f"ECDSA Digital Signature: {signature_hex}\n"
           f"Status: {status_badge}\n\n"
           f"Your ballot is cryptographically tamper-evident and can be audited on the public blockchain explorer."
           if is_success else
           f"Reason: {failure_reason}\n\n"
           f"If you did not initiate this vote attempt, please report it to the SRU Electoral Commission.")
        + f"\n\nThank you,\nSRU Blockchain Electoral Commission"
    )
    msg.set_content(plain_content)

    # Details rows for HTML email
    if is_success:
        receipt_rows = f'''\
            <tr><td style="padding: 10px; font-weight: bold; color: #555; width: 170px;">Voter Name:</td><td style="padding: 10px; color: #111;">{voter_name}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px; font-weight: bold; color: #555;">Masked Aadhaar:</td><td style="padding: 10px; font-family: monospace; color: #111;">{masked_aadhaar}</td></tr>
            <tr><td style="padding: 10px; font-weight: bold; color: #555;">Chosen Candidate:</td><td style="padding: 10px; font-weight: bold; color: #1e293b;">{candidate_name}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px; font-weight: bold; color: #555;">Political Party:</td><td style="padding: 10px; color: #111;">{party_name}</td></tr>
            <tr><td style="padding: 10px; font-weight: bold; color: #555;">Timestamp:</td><td style="padding: 10px; color: #555;">{timestamp_str}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px; font-weight: bold; color: #555;">Ballot Hash (SHA3-256):</td><td style="padding: 10px; font-family: monospace; font-size: 11px; word-break: break-all; color: #0284c7;">{ballot_hash}</td></tr>
            <tr><td style="padding: 10px; font-weight: bold; color: #555;">ECDSA P-256 Signature:</td><td style="padding: 10px; font-family: monospace; font-size: 11px; word-break: break-all; color: #7e22ce;">{signature_hex}</td></tr>
        '''
    else:
        receipt_rows = f'''\
            <tr><td style="padding: 10px; font-weight: bold; color: #555; width: 170px;">Voter Name:</td><td style="padding: 10px; color: #111;">{voter_name}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px; font-weight: bold; color: #555;">Masked Aadhaar:</td><td style="padding: 10px; font-family: monospace; color: #111;">{masked_aadhaar}</td></tr>
            <tr><td style="padding: 10px; font-weight: bold; color: #555;">Timestamp:</td><td style="padding: 10px; color: #555;">{timestamp_str}</td></tr>
            <tr style="background: #fef2f2;"><td style="padding: 10px; font-weight: bold; color: #991b1b;">Rejection Reason:</td><td style="padding: 10px; color: #991b1b; font-weight: 500;">{failure_reason}</td></tr>
        '''

    msg.add_alternative(f'''\
        <!DOCTYPE html>
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px; color: #333;">
                <div style="max-width: 620px; margin: auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e5e7eb;">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #7e22ce, #4c1d95); padding: 25px; text-align: center; color: white;">
                        <h2 style="margin: 0; font-size: 22px; letter-spacing: 0.5px;">SRU Blockchain E-Voting System</h2>
                        <span style="font-size: 13px; opacity: 0.9;">Official Electoral Commission • Digital Receipt</span>
                    </div>

                    <!-- Status Pill -->
                    <div style="padding: 25px 30px;">
                        <div style="text-align: center; margin-bottom: 20px;">
                            <span style="background: {status_color}; color: white; padding: 6px 18px; border-radius: 20px; font-size: 12px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;">
                                {status_badge}
                            </span>
                            <h3 style="margin: 15px 0 8px 0; color: #111; font-size: 19px;">{status_heading}</h3>
                        </div>

                        <p style="font-size: 14px; line-height: 1.6; color: #444;">
                            {status_msg}
                        </p>

                        <!-- Ballot Receipt Table -->
                        <div style="margin: 25px 0; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                            <div style="background: #f8fafc; padding: 10px 15px; border-bottom: 1px solid #e5e7eb; font-weight: bold; font-size: 13px; color: #334155;">
                                📜 Cryptographic Ballot Specifications
                            </div>
                            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                                {receipt_rows}
                            </table>
                        </div>

                        <div style="background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 8px; padding: 14px; margin-top: 20px; font-size: 12px; color: #6b21a8; line-height: 1.5;">
                            🔒 <strong>Blockchain Security Guarantee:</strong> This ballot was cryptographically verified using Elliptic Curve Digital Signatures (ECDSA P-256) and hashed using SHA3-256. It is tamper-evident and permanently auditable on the decentralized ledger.
                        </div>
                    </div>

                    <!-- Footer -->
                    <div style="background: #f9fafb; padding: 15px 20px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 12px; color: #6b7280;">
                        <p style="margin: 0;">SR University • School of Computer Science & Engineering</p>
                        <p style="margin: 4px 0 0 0; font-size: 11px; color: #9ca3af;">Decentralized Electronic Voting Platform • Academic Year 2025–2026</p>
                    </div>
                </div>
            </body>
        </html>
    ''', subtype='html')

    ok, err = _dispatch_smtp_message(email_address, email_password, msg)
    if ok:
        print(f"\n[REAL-TIME CONFIRMATION DELIVERED] Successfully sent vote confirmation to: {email_to}\n")
        return [True, "Delivered"]
    else:
        logger.warning(f"SMTP confirmation delivery to {email_to} failed: {err}")
        return [False, str(err)]
