import sendgrid
import os
from sendgrid.helpers.mail import Mail

os.environ['SENDGRID_API_KEY'] = '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'

message = Mail(
    from_email='zentivra0@gmail.com',
    to_emails='bhuvanboddu08@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
try:
    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)
