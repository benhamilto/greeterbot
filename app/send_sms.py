from twilio.rest import Client

account_sid = 'AC4fb1b3b438e134f3f50b2bb9c634214c'
auth_token = '2f1b7b9ede52e6d7f82b11e8552289c1'
client = Client(account_sid, auth_token)

message = client.messages.create(
                     body="Join Earth's mightiest heroes. Like Kevin Bacon.",
                     from_='+19029075449',
                     to='+14039901134'
                 )

print(message.sid)