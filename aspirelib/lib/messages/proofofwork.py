#! /usr/bin/python3

import decimal
import logging
logger = logging.getLogger(__name__)

from aspirelib.lib import config
from aspirelib.lib import exceptions
from aspirelib.lib import log
from aspirelib.lib import util


"""Match {} PoW to payout {}.""".format(config.BTC, config.XCP)

D = decimal.Decimal
ID = 60


def initialise(db):
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS proofofwork(
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      address TEXT,
                      mined INTEGER,
                      status TEXT)
                   ''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS status_idx ON proofofwork (status)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS address_idx ON proofofwork (address)''')


def validate(db, address, quantity, block_index):
    problems = []

    if block_index is None:
        problems.append('Must include block_index')

    if not config.TESTNET and block_index > 1:
        problems.append('No more ASP after premine on mainnet')

    if not isinstance(quantity, int):
        problems.append('quantity must be in satoshis')
        return problems

    if quantity < 0:
        problems.append('negative quantity')

    return problems


def compose(db, address, quantity):
    problems = validate(db, address, quantity, util.CURRENT_BLOCK_INDEX)
    if problems:
        raise exceptions.ComposeError(problems)
    return address, quantity


def parse(db, address, quantity, block_index, tx_hash):
    cursor = db.cursor()

    problems = validate(db, address, quantity, block_index)
    if not problems:
        sql = 'INSERT INTO proofofwork VALUES(:tx_hash, :block_index, :address, :mined, :status)'
        cursor.execute(sql, {
            'tx_hash': tx_hash,
            'block_index': block_index,
            'address': address,
            'mined': quantity,
            'status': 'pending',
        })
    cursor.close()


def confirm(db, block_index):
    # Credit source address with earned ASP.
    cursor = db.cursor()
    to_payout = list(cursor.execute('''SELECT * FROM proofofwork WHERE (block_index <= ? AND status = ?)''', (block_index - 100, 'pending')))
    for payout in to_payout:
        sql = 'UPDATE proofofwork SET status=:status WHERE block_index == :block_index'
        cursor.execute(sql, {
            'block_index': payout['block_index'],
            'status': 'confirmed'
        })
        util.credit(db, payout['address'], config.XCP, payout['mined'], action='proofofwork', event=str(block_index))
    cursor.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
