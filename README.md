# Description
`aspire-lib` is the reference implementation of the [Aspire Protocol](https://aspirecrypto.com).

Ubuntu 16.04 Build Instructions
-------------------
**Note:** for the command-line interface to `aspire-lib`(https://github.com/AspireOrg/aspire-lib), see [`aspire-cli`](https://github.com/AspireOrg/aspire-cli).

Install Python3.5.6
=======
```
sudo apt install -y build-essential checkinstall
sudo apt install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libssl-dev
cd /tmp
wget https://www.python.org/ftp/python/3.5.6/Python-3.5.6.tgz
tar xzf Python-3.5.6.tgz
cd Python-3.5.6
sudo ./configure --enable-optimizations
sudo make altinstall
```

(optional) Create aspire user. (every command following this should be used as this user, run all aspire software in its own user)
```
sudo adduser aspire --disabled-password
```

Setup virtualenv
```
cd ~
python3.5 -m venv ./virt
source ~/virt/bin/activate
```

Clone aspire-lib
```
cd ~
source ~/virt/bin/activate
git clone https://github.com/AspireOrg/aspire-lib.git
cd aspire-lib
pip install -r requirements.txt
python setup.py install
```

Followed by `aspire-cli`:
```
cd ~
source ~/virt/bin/activate
git clone https://github.com/AspireOrg/aspire-cli.git
cd aspire-cli
pip install -r requirements.txt
python setup.py install
```

# Basic Usage

Everything in this section assumes you've followed the setup and install from above. Be sure to always enter your python virtualenv
```
source ~/virt/bin/activate
```

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
python
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
