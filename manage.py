import argparse
import models
import updater
import garmin
from getpass import getpass
from dateutil.parser import parse as parse_date
import logger


log = logger.getLogger(__name__)


parser = argparse.ArgumentParser()
parser.add_argument("--action", help="action to execute", required=True, choices=['add-account', 'test'])
args = parser.parse_known_args()[0]

if args.action == 'add-account':
    nickname = raw_input('Nickname: ')
    while True:
        try:
            start_date = parse_date(raw_input('Start date (YYYY/mm/dd): ')).date()
            break
        except:
            print 'Use the format YYYY/mm/dd'

    fitbit_creds = dict()
    fitbit_creds['username'] = raw_input('Fitbit Username: ')
    fitbit_creds['password'] = getpass()

    garmin_creds = dict()
    garmin_creds['username'] = raw_input('Garmin Username: ')
    garmin_creds['password'] = getpass()

    fitbit_creds = models.FitbitCredentials(**fitbit_creds)
    garmin_creds = models.ServiceCredentials(**garmin_creds)
    account = models.Account(nickname=nickname, fitbit_creds=fitbit_creds, garmin_creds=garmin_creds,
                             start_date=start_date)
    account.save()
elif args.action == 'test':
    for account in models.Account.objects:
        log.debug('Processing account %s' % account.nickname)
        # with garmin.GarminClient(account) as garmin_client:
        #     garmin_client.delete_all_weights()
        upd = updater.Updater(account)
        upd.update()
