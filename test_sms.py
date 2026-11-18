#!/usr/bin/env python
"""
Diagnostic utility to test Real-Time Mobile SMS OTP delivery to mobile phones.
Usage:
    py test_sms.py [phone_number]

Example:
    py test_sms.py 6302559916
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Election.settings')
django.setup()

from django.conf import settings
from home.methods_module import send_mobile_otp

def main():
    recipient_phone = sys.argv[1] if len(sys.argv) > 1 else '6302559916'
    
    fast2sms_key = getattr(settings, 'FAST2SMS_API_KEY', '').strip()
    twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '').strip()
    twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '').strip()
    twilio_from = getattr(settings, 'TWILIO_PHONE_NUMBER', '').strip()
    twofactor_key = getattr(settings, 'TWOFACTOR_API_KEY', '').strip()

    print("=" * 65)
    print("SECUREVOTE BLOCKCHAIN: REAL-TIME MOBILE SMS DIAGNOSTIC")
    print("=" * 65)
    print(f"Target Mobile:   +91 {recipient_phone}")
    print(f"Fast2SMS Key:    {'CONFIGURED (' + fast2sms_key[:6] + '...)' if fast2sms_key else '[NOT SET]'}")
    print(f"Twilio SID:      {'CONFIGURED' if twilio_sid else '[NOT SET]'}")
    print(f"Twilio Number:   {twilio_from if twilio_from else '[NOT SET]'}")
    print(f"2Factor Key:     {'CONFIGURED' if twofactor_key else '[NOT SET]'}")
    print("=" * 65)

    has_gateway = bool(fast2sms_key or (twilio_sid and twilio_token and twilio_from) or twofactor_key)

    if not has_gateway:
        print("\n⚠️ No real-time SMS Gateway API key is currently configured!")
        print("\nTo receive real SMS on your mobile phone:")
        print("1. Sign up for free at: https://www.fast2sms.com")
        print("2. Copy your API Key from Dev API tab")
        print("3. Add to your .env file: FAST2SMS_API_KEY=your_copied_key")
        print("4. Re-run this test: py test_sms.py " + recipient_phone)
        print("\nRunning in Demo Mode fallback for now...")
    else:
        print(f"\nAttempting live SMS dispatch to +91 {recipient_phone} ...")

    res = send_mobile_otp(recipient_phone)

    if res[0] and not res[2]:
        print(f"\n🎉 SUCCESS! Real-time SMS OTP was sent to +91 {recipient_phone}!")
        print(f"OTP Code: {res[1]}")
        print("Please check your phone's SMS inbox.")
    else:
        print(f"\n⚠️ System operated in Demo Mode.")
        print(f"Generated OTP: {res[1]}")

if __name__ == '__main__':
    main()
