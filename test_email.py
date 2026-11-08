#!/usr/bin/env python
"""
Diagnostic utility to test Real-Time Email delivery via Gmail / SMTP.
Usage:
    python test_email.py [recipient_email]

Example:
    python test_email.py 2303a51751@sru.edu.in
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Election.settings')
django.setup()

from django.conf import settings
from home.methods_module import send_email_otp

def main():
    recipient = sys.argv[1] if len(sys.argv) > 1 else '2303a51751@sru.edu.in'
    
    sender = getattr(settings, 'EMAIL_ADDRESS', '').strip()
    pwd = getattr(settings, 'EMAIL_PASSWORD', '').strip()
    host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
    port = getattr(settings, 'EMAIL_PORT', 465)

    print("=" * 65)
    print("SRU BLOCKCHAIN E-VOTING: REAL-TIME SMTP DIAGNOSTIC TEST")
    print("=" * 65)
    print(f"SMTP Host:      {host}")
    print(f"SMTP Port:      {port}")
    print(f"Sender Email:   {sender if sender else '[NOT SET IN .env]'}")
    print(f"Password Set:   {'YES (' + str(len(pwd.replace(' ', ''))) + ' chars)' if pwd else '[NOT SET IN .env]'}")
    print(f"Test Recipient: {recipient}")
    print("=" * 65)

    if not sender or not pwd:
        print("\n❌ ERROR: EMAIL_ADDRESS and EMAIL_PASSWORD are not configured in .env!")
        print("\nTo send real-time OTPs to inboxes:")
        print("1. Open .env")
        print("2. Set EMAIL_ADDRESS=your_email@gmail.com")
        print("3. Set EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  (16-character Google App Password)")
        print("   Get App Password at: https://myaccount.google.com/apppasswords")
        print("4. Re-run this script: python test_email.py " + recipient)
        sys.exit(1)

    print(f"\nAttempting real-time OTP delivery to: {recipient} ...")
    res = send_email_otp(recipient)

    if res[0] and not res[2]:
        print(f"\n🎉 SUCCESS! Real-time OTP was sent to {recipient}'s inbox!")
        print(f"Generated OTP: {res[1]}")
        print("Please check the inbox (or spam folder) for the verification email.")
    else:
        print(f"\n⚠️ Delivery fell back to Demo Mode.")
        print(f"OTP generated: {res[1]}")
        print("Check the error logs above for SMTP connection or authentication issues.")

if __name__ == '__main__':
    main()

