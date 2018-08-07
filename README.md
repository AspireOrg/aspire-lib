[![Build Status Travis](https://travis-ci.org/AspireOrg/aspire-lib.svg?branch=develop)](https://travis-ci.org/AspireOrg/aspire-lib)
[![Build Status Circle](https://circleci.com/gh/AspireOrg/aspire-lib.svg?&style=shield)](https://circleci.com/gh/AspireOrg/aspire-lib)
[![Coverage Status](https://coveralls.io/repos/AspireOrg/aspire-lib/badge.png?branch=develop)](https://coveralls.io/r/AspireOrg/aspire-lib?branch=develop)
[![Latest Version](https://pypip.in/version/aspire-lib/badge.svg)](https://pypi.python.org/pypi/aspire-lib/)
[![License](https://pypip.in/license/aspire-lib/badge.svg)](https://pypi.python.org/pypi/aspire-lib/)
[![Docker Pulls](https://img.shields.io/docker/pulls/aspireorg/aspire-server.svg?maxAge=2592000)](https://hub.docker.com/r/aspireorg/aspire-server/)


# Description
`aspire-lib` is the reference implementation of the [Aspire Protocol](https://aspirecrypto.com).

**Note:** for the command-line interface to `aspire-lib`, see [`aspire-cli`](https://github.com/AspireOrg/aspire-cli).


# Installation

For a simple Docker-based install of the Aspire software stack, see [this guide](http://counterparty.io/docs/federated_node/).


# Manual installation

Download the newest [AspireGas Core](https://github.com/AspireOrg/aspiregas/releases) and create
a `aspiregas.conf` file with the following options:

```
rpcuser=aspiregasrpc
rpcpassword=rpc
server=1
txindex=1
addrindex=1
rpctimeout=300
```

**Note:** you can and should replace the RPC credentials. Remember to use the changed RPC credentials throughout this document.

Then, download and install `aspire-lib`:

```
$ git clone https://github.com/AspireOrg/aspire-lib.git
$ cd aspire-lib
$ sudo pip3 install --upgrade -r requirements.txt
$ sudo python3 setup.py install
```

Followed by `aspire-cli`:

```
$ git clone https://github.com/AspireOrg/aspire-cli.git
$ cd aspire-cli
$ sudo pip3 install --upgrade -r requirements.txt
$ sudo python3 setup.py install
```

Note on **sudo**: both aspire-lib and aspire-server can be installed by non-sudoers. Please refer to external documentation for instructions on using pip without root access and other information related to custom install locations.


Then, launch the daemon via:

```
$ aspire-server bootstrap
$ aspire-server --backend-password=rpc start
```

# Basic Usage

## Via command-line 

(Requires `aspire-cli` to be installed.)

* The first time you run the server, you may bootstrap the local database with:
	`$ aspire-server bootstrap`

* Start the server with:
	`$ aspire-server start`

* Check the status of the server with:
	`$ aspire-client getinfo`

* For additional command-line arguments and options:
	`$ aspire-server --help`
	`$ aspire-client --help`

## Via Python

Bare usage from Python is also possible, without installing `aspire-cli`:

```
$ python3
>>> from aspirelib import server
>>> db = server.initialise(<options>)
>>> server.start_all(db)
```

# Configuration and Operation

The paths to the **configuration** files, **log** files and **database** files are printed to the screen when starting the server in ‘verbose’ mode:
	`$ aspire-server --verbose start`

By default, the **configuration files** are named `server.conf` and `client.conf` and located in the following directories:

* Linux: `~/.config/aspire/`
* Windows: `%APPDATA%\Aspire\`

Client and Server log files are named `aspire.client.[testnet.]log` and `aspire.server.[testnet.]log`, and located in the following directories:

* Linux: `~/.cache/aspire/log/`
* Windows: `%APPDATA%\Local\Aspire\aspire\Logs`

Aspire API activity is logged in `server.[testnet.]api.log` and `client.[testnet.]api.log`.

Aspire database files are by default named `aspire.[testnet.]db` and located in the following directories:

* Linux: `~/.local/share/aspire`
* Windows: `%APPDATA%\Roaming\Aspire\aspire`

## Configuration File Format

Manual configuration is not necessary for most use cases. "back-end" and "wallet" are used to access AspireGas server RPC.

A `aspire-server` configuration file looks like this:

	[Default]
	backend-name = addrindex
	backend-user = <user>
	backend-password = <password>
	rpc-host = 0.0.0.0
	rpc-user = <rpcuser>
	rpc-password = <rpcpassword>

The ``force`` argument can be used either in the server configuration file or passed at runtime to make the server keep running in the case it loses connectivity with the Internet and falls behind the back-end database. This may be useful for *non-production* Aspire servers that need to maintain RPC service availability even when the backend or aspire server has no Internet connectivity.

A `aspire-client` configuration file looks like this:

	[Default]
	wallet-name = aspiregascore
	wallet-connect = localhost
	wallet-user = <user>
	wallet-password = <password>
	aspire-rpc-connect = localhost
	aspire-rpc-user = <rpcuser>
	aspire-rpc-password = <password>


# Developer notes

## Versioning

* Major version changes require a full (automatic) rebuild of the database.
* Minor version changes require a(n automatic) database reparse.
* All protocol changes are retroactive on testnet.

## Continuous integration
 - TravisCI is setup to run all tests with 1 command and generate a coverage report and let `python-coveralls` parse and upload it.
   It does runs with `--skiptestbook=all` so it will not do the reparsing of the bootstrap files.
 - CircleCI is setup to split the tests as much as possible to make it easier to read the error reports.
   It also runs the `integration_test.test_book` tests, which reparse the bootstrap files.


# Further Reading

* [Official Project Documentation](http://counterparty.io/docs/)
