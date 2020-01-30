from datetime import datetime
from dateutil.tz import tzlocal
from colorlog import ColoredFormatter
import bitcoin as bitcoinlib
import binascii
import collections
import decimal
import json
import time
import os
import logging

from aspirelib.lib import config
from aspirelib.lib import exceptions
from aspirelib.lib import util

D = decimal.Decimal
logger = logging.getLogger(__name__)


class ModuleLoggingFilter(logging.Filter):
    """
    module level logging filter (NodeJS-style), ie:
        filters="*,-aspirelib.lib,aspirelib.lib.api"

        will log:
         - aspirecli.server
         - aspirelib.lib.api

        but will not log:
         - aspirelib.lib
         - aspirelib.lib.backend.addrindex
    """

    def __init__(self, filters):
        self.filters = str(filters).split(",")

        self.catchall = "*" in self.filters
        if self.catchall:
            self.filters.remove("*")

    def filter(self, record):
        """
        Determine if specified record should be logged or not
        """
        result = None

        for filter in self.filters:
            if filter[:1] == "-":
                if result is None and ModuleLoggingFilter.ismatch(record, filter[1:]):
                    result = False
            else:
                if ModuleLoggingFilter.ismatch(record, filter):
                    result = True

        if result is None:
            return self.catchall

        return result

    @classmethod
    def ismatch(cls, record, name):
        """
        Determine if the specified record matches the name, in the same way as original logging.Filter does, ie:
            'aspirelib.lib' will match 'aspirelib.lib.check'
        """
        nlen = len(name)
        if nlen == 0:
            return True
        elif name == record.name:
            return True
        elif record.name.find(name, 0, nlen) != 0:
            return False
        return record.name[nlen] == "."


ROOT_LOGGER = None
def set_logger(logger):
    global ROOT_LOGGER
    if ROOT_LOGGER is None:
        ROOT_LOGGER = logger


LOGGING_SETUP = False
LOGGING_TOFILE_SETUP = False
def set_up(logger, verbose=False, logfile=None, console_logfilter=None):
    global LOGGING_SETUP
    global LOGGING_TOFILE_SETUP

    def set_up_file_logging():
        assert logfile
        max_log_size = 20 * 1024 * 1024  # 20 MB
        if os.name == 'nt':
            from aspirelib.lib import util_windows
            fileh = util_windows.SanitizedRotatingFileHandler(logfile, maxBytes=max_log_size, backupCount=5)
        else:
            fileh = logging.handlers.RotatingFileHandler(logfile, maxBytes=max_log_size, backupCount=5)
        fileh.setLevel(logging.DEBUG)
        LOGFORMAT = '%(asctime)s [%(levelname)s] %(message)s'
        formatter = logging.Formatter(LOGFORMAT, '%Y-%m-%d-T%H:%M:%S%z')
        fileh.setFormatter(formatter)
        logger.addHandler(fileh)

    if LOGGING_SETUP:
        if logfile and not LOGGING_TOFILE_SETUP:
            set_up_file_logging()
            LOGGING_TOFILE_SETUP = True
        logger.getChild('log.set_up').debug('logging already setup')
        return
    LOGGING_SETUP = True

    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # Console Logging
    console = logging.StreamHandler()
    console.setLevel(log_level)

    # only add [%(name)s] to LOGFORMAT if we're using console_logfilter
    LOGFORMAT = '%(log_color)s[%(asctime)s][%(levelname)s]' + ('' if console_logfilter is None else '[%(name)s]') + ' %(message)s%(reset)s'
    LOGCOLORS = {'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red'}
    formatter = ColoredFormatter(LOGFORMAT, "%Y-%m-%d %H:%M:%S", log_colors=LOGCOLORS)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if console_logfilter:
        console.addFilter(ModuleLoggingFilter(console_logfilter))

    # File Logging
    if logfile:
        set_up_file_logging()
        LOGGING_TOFILE_SETUP = True

    # Quieten noisy libraries.
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(log_level)
    requests_log.propagate = False
    urllib3_log = logging.getLogger('urllib3')
    urllib3_log.setLevel(log_level)
    urllib3_log.propagate = False

    # Disable InsecureRequestWarning
    import requests
    requests.packages.urllib3.disable_warnings()


def curr_time():
    return int(time.time())


def isodt(epoch_time):
    try:
        return datetime.fromtimestamp(epoch_time, tzlocal()).isoformat()
    except OSError:
        return '<datetime>'


def message(db, block_index, command, category, bindings, tx_hash=None):
    cursor = db.cursor()

    # Get last message index.
    messages = list(cursor.execute('''SELECT * FROM messages
                                      WHERE message_index = (SELECT MAX(message_index) from messages)'''))
    if messages:
        assert len(messages) == 1
        message_index = messages[0]['message_index'] + 1
    else:
        message_index = 0

    # Not to be misleading…
    if block_index == config.MEMPOOL_BLOCK_INDEX:
        try:
            del bindings['status']
            del bindings['block_index']
            del bindings['tx_index']
        except KeyError:
            pass

    # Handle binary data.
    items = []
    for item in sorted(bindings.items()):
        if type(item[1]) == bytes:
            items.append((item[0], binascii.hexlify(item[1]).decode('ascii')))
        else:
            items.append(item)

    bindings_string = json.dumps(collections.OrderedDict(items))
    cursor.execute('insert into messages values(:message_index, :block_index, :command, :category, :bindings, :timestamp)',
                   (message_index, block_index, command, category, bindings_string, curr_time()))

    # Log only real transactions.
    if block_index != config.MEMPOOL_BLOCK_INDEX:
        log(db, command, category, bindings)

    cursor.close()


def log(db, command, category, bindings):

    cursor = db.cursor()

    for element in bindings.keys():
        try:
            str(bindings[element])
        except KeyError:
            bindings[element] = '<Error>'

    # Slow?!
    def output(quantity, asset):
        try:
            if asset not in ('fraction', 'leverage'):
                return str(util.value_out(db, quantity, asset)) + ' ' + asset
            else:
                return str(util.value_out(db, quantity, asset))
        except exceptions.AssetError:
            return '<AssetError>'
        except decimal.DivisionByZero:
            return '<DivisionByZero>'
        except TypeError:
            return '<None>'

    if command == 'update':
        if category == 'proofofwork':
            logger.info('POW: block {} {}'.format(bindings['block_index'], bindings['status']))

        # TODO: elif category == 'balances':
            # logger.debug('Database: set balance of {} in {} to {}.'.format(bindings['address'], bindings['asset'], output(bindings['quantity'], bindings['asset']).split(' ')[0]))

    elif command == 'insert':

        if category == 'credits':
            logger.debug('Credit: {} to {} #{}# <{}>'.format(output(bindings['quantity'], bindings['asset']), bindings['address'], bindings['action'], bindings['event']))

        elif category == 'debits':
            logger.debug('Debit: {} from {} #{}# <{}>'.format(output(bindings['quantity'], bindings['asset']), bindings['address'], bindings['action'], bindings['event']))

        elif category == 'sends':
            logger.info('Send: {} from {} to {} ({}) [{}]'.format(output(bindings['quantity'], bindings['asset']), bindings['source'], bindings['destination'], bindings['tx_hash'], bindings['status']))

        elif category == 'issuances':
            if bindings['transfer']:
                logger.info('Issuance: {} transfered asset {} to {} ({}) [{}]'.format(bindings['source'], bindings['asset'], bindings['issuer'], bindings['tx_hash'], bindings['status']))
            elif bindings['locked']:
                logger.info('Issuance: {} locked asset {} ({}) [{}]'.format(bindings['issuer'], bindings['asset'], bindings['tx_hash'], bindings['status']))
            else:
                if bindings['divisible']:
                    divisibility = 'divisible'
                else:
                    divisibility = 'indivisible'
                try:
                    quantity = util.value_out(db, bindings['quantity'], None, divisible=bindings['divisible'])
                except:
                    quantity = '?'
                if 'asset_longname' in bindings and bindings['asset_longname'] is not None:
                    logger.info('Subasset Issuance: {} created {} of {} subasset {} as numeric asset {} ({}) [{}]'.format(bindings['issuer'], quantity, divisibility, bindings['asset_longname'], bindings['asset'], bindings['tx_hash'], bindings['status']))
                else:
                    logger.info('Issuance: {} created {} of {} asset {} ({}) [{}]'.format(bindings['issuer'], quantity, divisibility, bindings['asset'], bindings['tx_hash'], bindings['status']))

        elif category == 'broadcasts':
            if bindings['locked']:
                logger.info('Broadcast: {} locked his feed ({}) [{}]'.format(bindings['source'], bindings['tx_hash'], bindings['status']))
            else:
                logger.info('Broadcast: ' + bindings['source'] + ' at ' + isodt(bindings['timestamp']) + ' with a fee of {}%'.format(output(D(bindings['fee_fraction_int'] / 1e8) * D(100), 'fraction')) + ' (' + bindings['tx_hash'] + ')' + ' [{}]'.format(bindings['status']))

        elif category == 'dividends':
            logger.info('Dividend: {} paid {} per unit of {} ({}) [{}]'.format(bindings['source'], output(bindings['quantity_per_unit'], bindings['dividend_asset']), bindings['asset'], bindings['tx_hash'], bindings['status']))

        elif category == 'proofofwork':
            logger.info('POW: [{}] {} mined {} (txid {})'.format(bindings['status'], bindings['address'], output(bindings['mined'], config.XCP), bitcoinlib.core.b2lx(bindings['tx_hash'])))

        elif category == 'cancels':
            logger.info('Cancel: {} ({}) [{}]'.format(bindings['offer_hash'], bindings['tx_hash'], bindings['status']))

        elif category == 'contracts':
            logger.info('New Contract: {}'.format(bindings['contract_id']))

        elif category == 'executions':
            """
            try:
                payload_hex = binascii.hexlify(bindings['payload']).decode('ascii')
            except TypeError:
                payload_hex = '<None>'
            try:
                output_hex = binascii.hexlify(bindings['output']).decode('ascii')
            except TypeError:
                output_hex = '<None>'
            logger.info('Execution: {} executed contract {}, funded with {}, at a price of {} (?), at a final cost of {}, reclaiming {}, and also sending {}, with a data payload of {}, yielding {} ({}) [{}]'.format(bindings['source'], bindings['contract_id'], output(bindings['gas_start'], config.XCP), bindings['gas_price'], output(bindings['gas_cost'], config.XCP), output(bindings['gas_remaining'], config.XCP), output(bindings['value'], config.XCP), payload_hex, output_hex, bindings['tx_hash'], bindings['status']))
            """
            if bindings['contract_id']:
                logger.info('Execution: {} executed contract {} ({}) [{}]'.format(bindings['source'], bindings['contract_id'], bindings['tx_hash'], bindings['status']))
            else:
                logger.info('Execution: {} created contract {} ({}) [{}]'.format(bindings['source'], bindings['output'], bindings['tx_hash'], bindings['status']))

        elif category == 'destructions':
            logger.info('Destruction: {} destroyed {} {} with tag ‘{}’({}) [{}]'.format(bindings['source'], bindings['quantity'], bindings['asset'], bindings['tag'], bindings['tx_hash'], bindings['status']))

    cursor.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
