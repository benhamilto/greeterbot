import os
from datetime import timedelta


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SECRET_CODE = os.environ.get('SECRET_CODE')
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=1800)
    TWILIO_ACCOUNT_SID = os.environ['account_sid']
    TWILIO_AUTH_TOKEN = os.environ['auth_token']
