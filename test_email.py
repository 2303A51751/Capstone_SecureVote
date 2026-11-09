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
    brevo_key = getattr(settings, 'BREVO_API_KEY', '').strip()
    resend_key = getattr(settings, 'RESEND_API_KEY', '').strip()

    print("=" * 65)
    print("SECUREVOTE BLOCKCHAIN SYSTEM: REAL-TIME EMAIL DISPATCH DIAGNOSTIC")
    print("=" * 65)
    print(f"Brevo API Key:  {'CONFIGURED (HTTPS Port 443 - Render Ready)' if brevo_key else '[NOT SET]'}")
    print(f"Resend API Key: {'CONFIGURED (HTTPS Port 443 - Render Ready)' if resend_key else '[NOT SET]'}")
    print(f"SMTP Host:      {host}")
    print(f"SMTP Port:      {port}")
    print(f"Sender Email:   {sender if sender else '[NOT SET]'}")
    print(f"Password Set:   {'YES (' + str(len(pwd.replace(' ', ''))) + ' chars)' if pwd else '[NOT SET]'}")
    print(f"Test Recipient: {recipient}")
    print("=" * 65)

    if not brevo_key and not resend_key and (not sender or not pwd):
        print("\n❌ ERROR: No email dispatch service is configured!")
        print("\nOptions to send live emails:")
        print("1. FOR RENDER FREE TIER (Recommended):")
        print("   Sign up for free at https://www.brevo.com -> API Keys -> Create Key")
        print("   Add BREVO_API_KEY=your_key in Render Environment Variables (bypasses port blocks).")
        print("\n2. FOR LOCAL / UNBLOCKED HOSTS:")
        print("   Set EMAIL_ADDRESS=your_email@gmail.com and EMAIL_PASSWORD=xxxx xxxx xxxx xxxx in .env")
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

