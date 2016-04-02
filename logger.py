from logging import getLogger
import logging

logging.basicConfig(format='%(asctime)s %(name)-40s %(lineno)-3s %(levelname)-8s %(message)s')
logging.getLogger().setLevel(logging.DEBUG)
