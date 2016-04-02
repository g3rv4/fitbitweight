settings = {
    'mongo': {
        'db': 'fitbitweight',
        'host': '127.0.0.1'
    },
    'fitbit': {
        'client_id': '',
        'client_secret': '',
        'redirect_uri': ''
    },
    'garmin': {
        'login_url': 'https://connect.garmin.com/en-US/signin'
    },
    'selenium': {
        'browser': 'phantomjs',
        'browsers': {
            'phantomjs': {
                'driver_class': 'PhantomJS',
                'executable_path': '/usr/local/bin/phantomjs',
                'extra_args': {
                    'desired_capabilities': {
                        'phantomjs.page.settings.userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
                    }
                }
            },
            'chrome': {
                'driver_class': 'Chrome',
                'executable_path': ''
            }
        }
    }
}
