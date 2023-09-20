import json, smtplib, os
from email.message import EmailMessage

def notification(message):
    message = json.loads(message)
    
    mp3_fid = message["mp3_fid"]

    sender_address = os.environ.get("GMAIL_ADDRESS")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    receiver_address = message["username"]

    msg = EmailMessage()
    msg.set_content(f"Your MP3 is ready to download. File Id to download your mp3 is: {mp3_fid}")
    msg["Subject"] = "MP3 Download Ready"
    msg["From"] = sender_address
    msg["To"] = receiver_address

    session = smtplib.SMTP("smtp.office365.com", 587)
    session.starttls()
    session.login(sender_address, sender_password)
    session.send_message(msg, sender_address, receiver_address)
    session.quit()
    print("Mail Sent")