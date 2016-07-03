import fitbit
import garmin
import utils
import datetime

log = utils.get_logger(__name__)


class Updater(object):
    def __init__(self, account):
        self.account = account

    def update(self):
        fitbit_client = fitbit.FitbitClient(self.account)
        fitbit_client.verify_subscription()
        new_fitbit = fitbit_client.get_weights()

        with garmin.GarminClient(self.account) as garmin_client:
            old_fitbit = self.account.latest_fitbit.get('data', {})

            # detect additions on fitbit
            for logId in [i for i in new_fitbit if i not in old_fitbit]:
                item = new_fitbit[logId]
                garmin_client.add_weight(item['date'], item['weight'], item.get('fat'))

            self.account.latest_fitbit = {
                'datetime': datetime.datetime.now(),
                'data': new_fitbit
            }
            self.account.save()
