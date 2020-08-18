FROM aspireorg/federatednode

MAINTAINER Aspire Developers <admin@aspirecrypto.com>

# Install aspire-lib
COPY . /aspire-lib
WORKDIR /aspire-lib
RUN pip3 install -r requirements.txt
RUN python3 setup.py develop
RUN python3 setup.py install_apsw
RUN python3 setup.py install_serpent

# Install aspire-cli
# NOTE: By default, check out the aspire-cli master branch. You can override the BRANCH build arg for a different
# branch (as you should check out the same branch as what you have with aspire-lib, or a compatible one)
# NOTE2: In the future, aspire-lib and aspire-cli will go back to being one repo...
ARG CLI_BRANCH=master
ENV CLI_BRANCH ${CLI_BRANCH}
RUN git clone -b ${CLI_BRANCH} https://github.com/AspireOrg/aspire-cli.git /aspire-cli
WORKDIR /aspire-cli
RUN pip3 install -r requirements.txt
RUN python3 setup.py develop

# Additional setup
COPY docker/server.conf /root/.config/aspire/server.conf
COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod a+x /usr/local/bin/start.sh
WORKDIR /

# Pull the mainnet and testnet DB boostraps
# RUN aspire-server bootstrap --quiet
# RUN aspire-server --testnet bootstrap --quiet

EXPOSE 4000 14000

# NOTE: Defaults to running on mainnet, specify -e TESTNET=1 to start up on testnet
ENTRYPOINT ["start.sh"]

