import seleniumrequests
from config import settings


class MyDriver(object):
    def __enter__(self):
        browser_config = settings['selenium']['browsers'][settings['selenium']['browser']]
        klass = getattr(globals()['seleniumrequests'], browser_config['driver_class'])
        self.driver = klass(executable_path=browser_config['executable_path'], **browser_config.get('extra_args', {}))
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()
        self.driver.quit()

    def __getattr__(self, name):
        def method(*args, **kwargs):
            return getattr(self.driver, name)(*args, **kwargs)
        return method
