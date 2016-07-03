import seleniumrequests
from config import settings
import logging


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

if 'log_path' in settings and settings['log_path']:
    handler = logging.handlers.RotatingFileHandler(settings['log_path'])
    handler.setLevel(logging.WARNING)
else:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

handler.setFormatter(logging.Formatter(
    '%(asctime)s %(name)-40s-%(lineno)-4s %(levelname)-8s %(message)s'
))


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not len(logger.handlers):
        logger.addHandler(handler)
        logger.propagate = False

    return logger
