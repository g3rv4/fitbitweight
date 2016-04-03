from config import settings
from urlparse import urlparse
from selenium.webdriver.common.keys import Keys
from dateutil.relativedelta import relativedelta
import urllib
import utils
import datetime
import requests
import base64
import json
import logger


log = logger.getLogger(__name__)


class FitbitException(Exception):
    pass


class CouldNotAuthenticateFitbitException(FitbitException):
    pass


class ErrorQueryingApiFitbitException(FitbitException):
    def __init__(self, error_code, *args, **kwargs):
        super(ErrorQueryingApiFitbitException, self).__init__(*args, **kwargs)
        self.error_code = error_code

    def __str__(self):
        return 'Error code: %i' % self.error_code


class FitbitClient(object):
    def __init__(self, account):
        self.account = account
        self.creds = account.fitbit_creds

    def log_in(self, force_refresh=False):
        if force_refresh or not self.creds.refresh_token:
            log.debug('Starting full log in')
            with utils.MyDriver() as driver:
                log.debug('Opening page')
                driver.get('https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=%s&redirect_uri=%s&scope=weight' % (settings['fitbit']['client_id'], urllib.quote_plus(settings['fitbit']['redirect_uri'])))
                log.debug('Filling fields')
                email = driver.find_elements_by_name('email')[1]
                password = driver.find_elements_by_name('password')[1]
                email.send_keys(self.creds.username)
                password.send_keys(self.creds.password)
                password.send_keys(Keys.ENTER)
                allow_buttons = [b for b in driver.find_elements_by_css_selector('button') if b.text in ('Allow', 'Permitir')]
                if allow_buttons:
                    allow_buttons[0].click()
                log.debug('Submitted')
                url = driver.current_url

            url = urlparse(url)
            query_dict = dict([tuple(x.split('=')) for x in url.query.split('&')])

            response = requests.post('https://api.fitbit.com/oauth2/token', {
                'client_id': settings['fitbit']['client_id'],
                'grant_type': 'authorization_code',
                'redirect_uri': settings['fitbit']['redirect_uri'],
                'code': query_dict['code']
            }, headers={'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (settings['fitbit']['client_id'],
                                                                                  settings['fitbit']['client_secret']))})

            if response.status_code == 200:
                data = json.loads(response.text)
                self.creds.user_id = data['user_id']
                self.creds.refresh_token = data['refresh_token']
                self.creds.auth_token = data['access_token']
                self.creds.auth_expiration = datetime.datetime.now() + datetime.timedelta(seconds=data['expires_in'])
                self.creds.save()
                self.verify_subscription()
                log.debug('Grabbed refresh and auth tokens')
            else:
                log.error('Error authenticating')
                raise CouldNotAuthenticateFitbitException

    def get_auth_token(self, force_refresh=False):
        if force_refresh or not self.creds.auth_token or self.creds.auth_expiration > datetime.datetime.utcnow():
            log.debug('Refreshing auth token')
            response = requests.post('https://api.fitbit.com/oauth2/token', {
                'grant_type': 'refresh_token',
                'refresh_token': self.creds.refresh_token
            }, headers={'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (settings['fitbit']['client_id'],
                                                                                  settings['fitbit']['client_secret']))})
            if response.status_code != 200:
                # if it fails, try regenerating the refresh token
                log.debug('Failure refreshing, trying full login')
                self.log_in(True)
            elif response.status_code == 200:
                data = json.loads(response.text)
                self.creds.user_id = data['user_id']
                self.creds.refresh_token = data['refresh_token']
                self.creds.auth_token = data['access_token']
                self.creds.auth_expiration = datetime.datetime.now() + datetime.timedelta(seconds=data['expires_in'])
                self.creds.save()
                log.debug('Auth token refreshed')

        return self.creds.auth_token

    def send_method(self, url, f, **kwargs):
        response = f(url, self.get_auth_token(), **kwargs)

        if response.status_code == 401:
            log.debug('Unauthorized, refreshing auth token')
            response = f(url, self.get_auth_token(True), **kwargs)
        if response.status_code in (200, 201):
            data = json.loads(response.text)
            return data

        log.error('Unrecognised status code :S')
        raise ErrorQueryingApiFitbitException(response.status_code)

    def get(self, url):
        def get_response(url, token):
            return requests.get('https://api.fitbit.com/1/user/%s/%s' % (self.creds.user_id, url), headers={
                'Authorization': 'Bearer %s' % token
            })

        return self.send_method(url, get_response)

    def post(self, url, data):
        def do_post(url, token, data):
            return requests.post('https://api.fitbit.com/1/user/%s/%s' % (self.creds.user_id, url), data, headers={
                'Authorization': 'Bearer %s' % token
            })

        return self.send_method(url, do_post, data=data)

    def get_weights(self):
        current = self.account.start_date
        current = datetime.date(current.year, current.month, 1)
        items = {}
        while current < datetime.datetime.now().date():
            log.debug('Getting weigths for month starting on %s' % current.strftime('%m/%d/%Y'))
            current += relativedelta(months=1)
            data = self.get('body/log/weight/date/%s/1m.json' % current.strftime('%Y-%m-%d'))['weight']
            for item in data:
                item['logId'] = str(item['logId'])
            items.update({item['logId']: item for item in data})

        return items

    def verify_subscription(self):
        subscriptions = self.get('body/apiSubscriptions.json')
        if not subscriptions['apiSubscriptions']:
            self.post('body/apiSubscriptions/%s.json' % self.account.pk, {})
        print subscriptions
