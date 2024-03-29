"""Variables prefixed with `DEFAULT` should be able to be overridden by
configuration file and command‐line arguments."""

UNIT = 100000000        # The same across assets.


# Versions
VERSION_MAJOR = 9
VERSION_MINOR = 57
VERSION_REVISION = 0
VERSION_STRING = str(VERSION_MAJOR) + '.' + str(VERSION_MINOR) + '.' + str(VERSION_REVISION)


# Aspire protocol
TXTYPE_FORMAT = '>I'
SHORT_TXTYPE_FORMAT = 'B'

TWO_WEEKS = 2 * 7 * 24 * 3600
MAX_EXPIRATION = 4 * 2016   # Two months

MEMPOOL_BLOCK_HASH = 'mempool'
MEMPOOL_BLOCK_INDEX = 9999999


# SQLite3
MAX_INT = 2**63 - 1


# AspireGas Core
OP_RETURN_MAX_SIZE = 80  # bytes


# Currency agnosticism
BTC = 'GASP'
XCP = 'ASP'

BTC_NAME = 'AspireGas'
XCP_NAME = 'Aspire'
APP_NAME = XCP_NAME.lower()

DEFAULT_RPC_PORT_TESTNET = 14000
DEFAULT_RPC_PORT = 4000

DEFAULT_BACKEND_PORT_TESTNET = 19874
DEFAULT_BACKEND_PORT = 9874
DEFAULT_BACKEND_PORT_TESTNET_BTCD = 18334
DEFAULT_BACKEND_PORT_BTCD = 8334

UNSPENDABLE_TESTNET = 'mvCounterpartyXXXXXXXXXXXXXXW24Hef'
UNSPENDABLE_MAINNET = '1CounterpartyXXXXXXXXXXXXXXXUWLpVr'

FOUNDATION_ADDRESS_MAINNET = 'GZE6P3gyiyNdWdozuVJDZjAiEAGe2u8AWR'
FOUNDATION_ADDRESS_TESTNET = 'FvzKvSF9ZNLbtFW5SS8R4xHeFArue9hBuT'

ADDRESSVERSION_TESTNET = b'%'
P2SH_ADDRESSVERSION_TESTNET = b'&'
PRIVATEKEY_VERSION_TESTNET = b'*'

ADDRESSVERSION_MAINNET = b'&'
P2SH_ADDRESSVERSION_MAINNET = b'a'
PRIVATEKEY_VERSION_MAINNET = b'\x0f'  # value = struct.unpack('B', 15)

MAGIC_BYTES_TESTNET = b'\xe4\xcf\xcc\xe3'
MAGIC_BYTES_MAINNET = b'\xe4\xcf\xcc\xe2'

BLOCK_FIRST_TESTNET = 0
BLOCK_FIRST_TESTNET_HASH = 'c31087a63889941d7275ee5e7388ede36dec20690f3ec1e0a45cc0b8e5945d2c'

BLOCK_FIRST_MAINNET = 0
BLOCK_FIRST_MAINNET_HASH = '678d2a0d8fa8e6da234b6da33c53e919e62b92bf4234d5bad0f76237efb3728d'


# Protocol defaults
# NOTE: If the DUST_SIZE constants are changed, they MUST also be changed in aspireblockd/lib/config.py as well
    # TODO: This should be updated, given their new configurability.
# TODO: The dust values should be lowered by 90%, once transactions with smaller outputs start confirming faster: <https://github.com/mastercoin-MSC/spec/issues/192>
DEFAULT_REGULAR_DUST_SIZE = 5430         # TODO: This is just a guess. I got it down to 5530 satoshis.
DEFAULT_MULTISIG_DUST_SIZE = 7800        # <https://bitcointalk.org/index.php?topic=528023.msg7469941#msg7469941>
DEFAULT_OP_RETURN_VALUE = 0
DEFAULT_FEE_PER_KB = 1000               # sane/low default, also used as minimum when estimated fee is used
ESTIMATE_FEE_PER_KB = False               # when True will use `estimatefee` from bitcoind instead of DEFAULT_FEE_PER_KB
ESTIMATE_FEE_NBLOCKS = 3

# UI defaults
DEFAULT_FEE_FRACTION_REQUIRED = .0009   # 0.090%
DEFAULT_FEE_FRACTION_PROVIDED = .01    # 1.00%


DEFAULT_REQUESTS_TIMEOUT = 20   # 20 seconds
DEFAULT_RPC_BATCH_SIZE = 20     # A 1 MB block can hold about 4200 transactions.

# Custom exit codes
EXITCODE_UPDATE_REQUIRED = 5


DEFAULT_CHECK_ASSET_CONSERVATION = True

BACKEND_RAW_TRANSACTIONS_CACHE_SIZE = 20000
BACKEND_RPC_BATCH_NUM_WORKERS = 6

UNDOLOG_MAX_PAST_BLOCKS = 100 #the number of past blocks that we store undolog history

DEFAULT_UTXO_LOCKS_MAX_ADDRESSES = 1000
DEFAULT_UTXO_LOCKS_MAX_AGE = 3.0 #in seconds

ADDRESS_OPTION_REQUIRE_MEMO = 1
ADDRESS_OPTION_MAX_VALUE = ADDRESS_OPTION_REQUIRE_MEMO # Or list of all the address options

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
