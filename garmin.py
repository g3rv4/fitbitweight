import utils
import json
import datetime
from config import settings
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.keys import Keys
from time import sleep
from decimal import Decimal


log = utils.get_logger(__name__)


class GarminException(Exception):
    pass


class CouldNotAuthenticateGarminException(GarminException):
    pass


class CouldNotPostWeightGarminException(GarminException):
    pass


class CouldNotDeleteWeightGarminException(GarminException):
    pass


class GarminClient(object):
    def __init__(self, account):
        self.account = account
        self.creds = account.garmin_creds
        self.logged_in = False
        self.driver = utils.MyDriver()

    def __enter__(self):
        self.driver.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.__exit__(exc_type, exc_val, exc_tb)

    def miliseconds_to_date(self, ms):
        return datetime.datetime.utcfromtimestamp(ms/1000.0).date()

    def date_to_miliseconds(self, dt):
        dt = datetime.datetime(dt.year, dt.month, dt.day)
        epoch = datetime.datetime.utcfromtimestamp(0)
        return (dt - epoch).total_seconds() * 1000.0

    def log_in(self):
        if not self.logged_in:
            log.debug('Starting login')
            self.driver.get(settings['garmin']['login_url'])
            self.driver.switch_to_frame(self.driver.find_element_by_tag_name('iframe'))
            username = self.driver.find_element_by_id('username')
            password = self.driver.find_element_by_id('password')
            username.send_keys(self.creds.username)
            password.send_keys(self.creds.password)
            password.send_keys(Keys.ENTER)
            log.debug('Iframe form submitted')
            sleep(3)

            for i in range(0, 20):
                if settings['garmin']['login_url'] != self.driver.driver.current_url:
                    break
                sleep(0.5)
                log.debug('url has not changed, waiting')

            self.logged_in = settings['garmin']['login_url'] != self.driver.driver.current_url
            if not self.logged_in:
                log.error('Could not authenticate :S')
                raise CouldNotAuthenticateGarminException

    def get_weights(self):
        self.log_in()
        current = self.account.start_date
        current = datetime.date(current.year, current.month, 1)
        logs = {}
        while current < datetime.datetime.now().date():
            log.debug('Getting weigths for month starting on %s' % current.strftime('%m/%d/%Y'))
            end = current + relativedelta(months=1)
            response = self.driver.request('GET', 'https://connect.garmin.com/modern/proxy/userprofile-service/'
                                                  'userprofile/personal-information/weightWithOutbound/filterByDay?'
                                                  'from=%i&until=%i&_=%i' % (self.date_to_miliseconds(current),
                                                                             self.date_to_miliseconds(end),
                                                                             self.date_to_miliseconds(datetime.datetime.now())))

            current = end

            if response.status_code == 204:
                continue

            data = json.loads(response.text)
            for item in data:
                item['date'] = self.miliseconds_to_date(item['date'])
                item['weight'] = Decimal(Decimal(item['weight']) / 1000)

            logs.update({item['samplePk']: item for item in data})

        return logs

    def add_weight(self, date, weight, fat):
        self.log_in()

        response = self.driver.request('POST', 'https://connect.garmin.com/modern/proxy/weight-service/user-weight',
                                       data=json.dumps({
                                           'value': weight,
                                           'unitKey': 'kg',
                                           'date': date
                                       }), headers={'Content-Type': 'application/json'})

        if response.status_code != 204:
            raise CouldNotPostWeightGarminException

    def delete_all_weights(self):
        self.log_in()

        for item in self.get_weights().values():
            response = self.driver.request('POST', 'https://connect.garmin.com/modern/proxy/user-service-1.0/rest/health_data',
                                           params={'date': item['date'].strftime('%Y-%m-%d')},
                                           headers={
                                                "Accept": "application/json, text/javascript, */*; q=0.01",
                                                "Content-Length": "0",
                                                "X-Http-Method-Override": "DELETE",
                                           })

            if response.status_code not in (204, 200):
                raise CouldNotDeleteWeightGarminException
