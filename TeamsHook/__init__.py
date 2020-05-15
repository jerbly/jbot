import base64
import hashlib
import hmac
import json
import os
import re

import azure.functions as func

jira_host = os.getenv('jira_host')
security_token = str.encode(os.getenv('security_token'))

p = re.compile('[A-Z0-9]+-[0-9]+')


def _get_jira_link(msg: str) -> str:
    tickets = p.findall(msg)
    ticket_count = len(tickets)
    if ticket_count == 1:
        return f'<a href="http://{jira_host}/browse/{tickets[0]}">{tickets[0]}</a>'
    elif ticket_count > 1:
        return f'<a href="http://{jira_host}/issues/?jql=key%20in%20({",".join(tickets)})">' \
               f'Found {ticket_count} tickets</a>'
    return 'No tickets found'


def main(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == 'POST':
        auth = req.headers.get('Authorization').split(' ')[1]
        request_data = req.get_body()
        digest = hmac.new(base64.b64decode(security_token), msg=request_data, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest).decode()

        if auth == signature:
            data = req.get_json()
            message = data['text']
            return func.HttpResponse(json.dumps({
                'type': 'message',
                'text': _get_jira_link(message)
            }))
        else:
            return func.HttpResponse(json.dumps({
                "type": "message",
                "text": "Error: message sender cannot be authenticated."
            }))
