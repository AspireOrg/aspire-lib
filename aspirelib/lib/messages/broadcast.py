#! /usr/bin/python3

"""
Broadcast a message, with or without a price.

Multiple messages per block are allowed.

An address is a feed of broadcasts. Feeds may be locked with a broadcast whose
text field is identical to ‘lock’ (case insensitive).

fee_fraction: .05 ASP means 5%. It may be greater than 1, however; but
because it is stored as a four‐byte integer, it may not be greater than about
42.
"""
from bitcoin.core import VarIntSerializer
from fractions import Fraction
import struct
import decimal
import json
import logging
logger = logging.getLogger(__name__)

from aspirelib.lib import exceptions
from aspirelib.lib import config
from aspirelib.lib import util
from aspirelib.lib import log
from aspirelib.lib import message_type


D = decimal.Decimal

FORMAT = '>IdI'
LENGTH = 4 + 8 + 4
ID = 30
# NOTE: Pascal strings are used for storing texts for backwards‐compatibility.


def initialise(db):
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS broadcasts(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      timestamp INTEGER,
                      value REAL,
                      fee_fraction_int INTEGER,
                      text TEXT,
                      locked BOOL,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   ''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS
                      block_index_idx ON broadcasts (block_index)
                   ''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS
                      status_source_idx ON broadcasts (status, source)
                   ''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS
                      status_source_index_idx ON broadcasts (status, source, tx_index)
                   ''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS
                      timestamp_idx ON broadcasts (timestamp)
                   ''')


def validate(db, source, timestamp, value, fee_fraction_int, text, block_index):
    problems = []

    # For SQLite3
    if timestamp > config.MAX_INT or value > config.MAX_INT or fee_fraction_int > config.MAX_INT:
        problems.append('integer overflow')

    if util.enabled('max_fee_fraction'):
        if fee_fraction_int >= config.UNIT:
            problems.append('fee fraction greater than or equal to 1')
    else:
        if fee_fraction_int > 4294967295:
            problems.append('fee fraction greater than 42.94967295')

    if timestamp < 0:
        problems.append('negative timestamp')

    if not source:
        problems.append('null source address')

    # Check previous broadcast in this feed.
    cursor = db.cursor()
    broadcasts = list(cursor.execute('''SELECT * FROM broadcasts WHERE (status = ? AND source = ?) ORDER BY tx_index ASC''', ('valid', source)))
    cursor.close()
    if broadcasts:
        last_broadcast = broadcasts[-1]
        if last_broadcast['locked']:
            problems.append('locked feed')
        elif timestamp <= last_broadcast['timestamp']:
            problems.append('feed timestamps not monotonically increasing')

    if util.enabled('options_require_memo') and text and text.lower().startswith('options'):
        ops_spl = text.split(" ")
        if len(ops_spl) == 2:
            try:
                options_int = int(ops_spl.pop())

                if (options_int > config.MAX_INT) or (options_int < 0):
                    problems.append('integer overflow')
                elif options_int > config.ADDRESS_OPTION_MAX_VALUE:
                    problems.append('options out of range')
            except:
                problems.append('options not an integer')

    return problems


def compose(db, source, timestamp, value, fee_fraction, text):

    # Store the fee fraction as an integer.
    fee_fraction_int = int(fee_fraction * 1e8)

    problems = validate(db, source, timestamp, value, fee_fraction_int, text, util.CURRENT_BLOCK_INDEX)
    if problems:
        raise exceptions.ComposeError(problems)

    data = message_type.pack(ID)

    # always use custom length byte instead of problematic usage of 52p format and make sure to encode('utf-8') for length
    if util.enabled('broadcast_pack_text'):
        data += struct.pack(FORMAT, timestamp, value, fee_fraction_int)
        data += VarIntSerializer.serialize(len(text.encode('utf-8')))
        data += text.encode('utf-8')
    else:
        if len(text) <= 52:
            curr_format = FORMAT + '{}p'.format(len(text) + 1)
        else:
            curr_format = FORMAT + '{}s'.format(len(text))

        data += struct.pack(curr_format, timestamp, value, fee_fraction_int, text.encode('utf-8'))
    return (source, [], data)


def parse(db, tx, message):
    cursor = db.cursor()

    # Unpack message.
    try:
        if util.enabled('broadcast_pack_text'):
            timestamp, value, fee_fraction_int, rawtext = struct.unpack(FORMAT + '{}s'.format(len(message) - LENGTH), message)
            textlen = VarIntSerializer.deserialize(rawtext)
            text = rawtext[-textlen:]

            assert len(text) == textlen
        else:
            if len(message) - LENGTH <= 52:
                curr_format = FORMAT + '{}p'.format(len(message) - LENGTH)
            else:
                curr_format = FORMAT + '{}s'.format(len(message) - LENGTH)

            timestamp, value, fee_fraction_int, text = struct.unpack(curr_format, message)

        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            text = ''
        status = 'valid'
    except:
        timestamp, value, fee_fraction_int, text = 0, None, 0, None
        status = 'invalid: could not unpack'

    if status == 'valid':
        # For SQLite3
        timestamp = min(timestamp, config.MAX_INT)
        value = min(value, config.MAX_INT)

        problems = validate(db, tx['source'], timestamp, value, fee_fraction_int, text, tx['block_index'])
        if problems:
            status = 'invalid: ' + '; '.join(problems)

    # Lock?
    lock = False
    if text and text.lower() == 'lock':
        lock = True
        timestamp, value, fee_fraction_int, text = 0, None, None, None
    else:
        lock = False

    # Add parsed transaction to message-type–specific table.
    bindings = {
        'tx_index': tx['tx_index'],
        'tx_hash': tx['tx_hash'],
        'block_index': tx['block_index'],
        'source': tx['source'],
        'timestamp': timestamp,
        'value': value,
        'fee_fraction_int': fee_fraction_int,
        'text': text,
        'locked': lock,
        'status': status,
    }
    if "integer overflow" not in status:
        sql = 'insert into broadcasts values(:tx_index, :tx_hash, :block_index, :source, :timestamp, :value, :fee_fraction_int, :text, :locked, :status)'
        cursor.execute(sql, bindings)
    else:
        logger.warn("Not storing [broadcast] tx [%s]: %s" % (tx['tx_hash'], status))
        logger.debug("Bindings: %s" % (json.dumps(bindings), ))

    # stop processing if broadcast is invalid for any reason
    if util.enabled('broadcast_invalid_check') and status != 'valid':
        return

    # Options? if the status is invalid the previous if should have catched it
    if util.enabled('options_require_memo'):
        if text and text.lower().startswith('options'):
            ops_spl = text.split(" ")
            if len(ops_spl) == 2:
                change_ops = False
                options_int = 0
                try:
                    options_int = int(ops_spl.pop())
                    change_ops = True
                except:
                    pass

                if change_ops:
                    op_bindings = {'block_index': tx['block_index'],
                                   'address': tx['source'],
                                   'options': options_int}
                    sql = 'insert or replace into addresses(address, options, block_index) values(:address, :options, :block_index)'
                    cursor = db.cursor()
                    cursor.execute(sql, op_bindings)

    # stop processing if broadcast is invalid for any reason
    # @TODO: remove this check once broadcast_invalid_check has been activated
    if util.enabled('max_fee_fraction') and status != 'valid':
        return

    cursor.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
