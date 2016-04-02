from config import settings
from mongoengine import connect, Document, EmbeddedDocument, StringField, EmbeddedDocumentField, DateTimeField, \
    BooleanField, DictField

connect(**settings['mongo'])


class ServiceCredentials(EmbeddedDocument):
    username = StringField()
    password = StringField()
    meta = {'allow_inheritance': True}


class FitbitCredentials(ServiceCredentials):
    user_id = StringField()
    auth_token = StringField()
    auth_expiration = DateTimeField()
    refresh_token = StringField()


class Account(Document):
    nickname = StringField()
    active = BooleanField()
    start_date = DateTimeField()
    fitbit_creds = EmbeddedDocumentField(FitbitCredentials)
    garmin_creds = EmbeddedDocumentField(ServiceCredentials)
    latest_garmin = DictField()
    latest_fitbit = DictField()
