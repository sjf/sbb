#!/usr/bin/env python3

from sendgrid import SendGridAPIClient # type: ignore
from sendgrid.helpers.mail import Mail # type: ignore
from .shell import *
from .utils import *

_FILE = '~/.sendgrid_api_key'
def mail(to_address, subject, body):
  from_address = os.environ.get('SENDGRID_FROM', None)
  sg = SendGridAPIClient(_get_api_key())
  message = Mail(
      from_email=from_address,
      to_emails=to_address,
      subject=subject,
      html_content=body)
  log(f"Sending mail '{subject}' to {to_address}.")
  response = sg.send(message)
  if response.status_code != 202:
    log(f"Failed to send mail: response {response.status_code}\n{dictl(response.headers)}")

def _get_api_key():
  env_var = os.environ.get('SENDGRID_API_KEY', None)
  if env_var:
    return env_var
  if exists(_FILE):
    return read(_FILE)
  raise Exception(f"Could not read API key from {_FILE}")
