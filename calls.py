import os
from dotenv import load_dotenv
from twilio.rest import Client
from urllib.parse import quote

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

def make_call(phone, text="Напоминание принять лекарство"):
    try:
        url = os.environ['GET_XML_CLOUDFUNCTION'] + quote(text)

        call = client.calls.create(
                                url=url,
                                to=phone,
                                from_=os.environ['TWILIO_PHONE']
                            )
        print(call.sid)
        
        return True
    except:
        return False 