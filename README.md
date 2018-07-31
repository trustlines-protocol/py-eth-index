# eth-index

eth-index is an indexer for events on the ethereum blockchain. It imports events
into a postgresql database. It's a companion to the trustlines project relay
server component.

## Installation
Before trying to install py-eth-index, make sure you have the postgresql
development header files and library installed. On debian based systems this can
be done by running:
```
apt install libpq-dev
```

eth-index uses python 3.6 or up. Please make sure you have the required version
installed.

Please checkout the source code from github, cd into the checked out repo and
run:

```
pip install -c constraints.txt  .
```

## Initializing the database

Please setup a working postgres environment, i.e. set the PG* environment
variables and configure ~/.pgpass.

Then run
```
psql -f create-table.sql
```
to create the database tables.

## ethindex
ethindex is a command line program that is being used to run the actual syncing
process. It also uses the PG* variables in order to determine the postgres
server to connect to.

### ethindex importabi
Before importing events into the postgres database, the ABIs must be known.

`ethindex importabi` can be used to import ABIs into the postgres database. By
default it reads two json files `addresses.json` and `contracts.json` from the
current directory and adds them to the abis table. These files are the exact
files that the relay server also reads. Their location can be specified via the
`--addresses` and `-contracts` command line arguments.

Usgae:
```
Usage: ethindex importabi [OPTIONS]

Options:
  --addresses TEXT
  --contracts TEXT
  --help            Show this message and exit.
```

### ethindex runsync
`ethindex runsync` will start the actual synchronization process. On the first start it will read all of the abis and create one entry in the sync table containing all contract addresses.
It then imports all of the events into the postgres table `events`.

Usage
```
Usage: ethindex runsync [OPTIONS]

Options:
  --jsonrpc TEXT      jsonrpc URL to use
  --waittime INTEGER  time to sleep in milliseconds waiting for a new block
  --help              Show this message and exit.
```
## Status and Limitations
ethindex is alpha software.
- ethindex currently does not handle chain reorgs
- there currently is no way to add more contracts to index

XXXX
