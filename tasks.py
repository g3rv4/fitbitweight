from celery import Celery
from config import settings
from updater import Updater
import models
import json

app = Celery('tasks', broker=settings['celery']['broker'])
app.conf.CELERY_ACCEPT_CONTENT = ['json']
app.conf.CELERY_TASK_SERIALIZER = 'json'


@app.task
def process_subscription(data):
    data = json.loads(data)
    ids = set([s['subscriptionId'] for s in data])
    for account in models.Account.objects.filter(pk__in=ids):
        updater = Updater(account)
        updater.update()
