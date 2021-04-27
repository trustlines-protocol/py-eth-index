|Build Status| |Code style: black|

eth-index
=========

eth-index is an indexer for events on the ethereum blockchain. It
imports events into a postgresql database. It's a companion to the
trustlines project relay server component.

Installation
------------

Before trying to install py-eth-index, make sure you have the postgresql
development header files and library installed. On debian based systems
this can be done by running:

::

    apt install libpq-dev

eth-index uses python 3.8 or up. Please make sure you have the required
version installed.

Please checkout the source code from github, cd into the checked out
repo and run the folllowing pip command with a fresh virtualenv:

::

    pip install -c constraints.txt  .

.. Note:: On Mac Big Sur - if the installation is failing due to compilation errros, make sure that you use openssl, readline, zlib, sqlite libs from brew and not the one that come bundles with Mac OS. Make sure your **LDFLAGS** and **CPPFLAGS** are properly set. For more info read here: https://github.com/psycopg/psycopg2/issues/1200

Development
-----------

A complete development environment can be installed with:

::

    pip install -c constraints.txt -r requirements.txt
    pip install -c constraints.txt -e .

This installs black, flake8, mypy and tox among other things.

black
~~~~~
The source code is formatted with `black <https://github.com/psf/black>`__. If
you choose not to use the pre-commit hook, you should be able to format the
source code with ``black setup.py src``.

flake8
~~~~~~
We use flake8 to check for errors. Run ``flake8 src`` to check for errors.

mypy
~~~~
mypy is used to check for type errors. Run ``mypy --ignore-missing-imports
src`` to check manually.

tox
~~~
Running ``tox`` will run black, flake8, mypy and pytest locally.

Since we also do run some tests for postgres, the postgres database server must
be installed on the local machine. It doesn't have to be started though, since
the tests do start postgres with a temporary data directory.

On a debian based system ``apt install postgresql`` will install the postgresql
database.

pre-commit
~~~~~~~~~~

The repository comes with a configuration file for `pre-commit
<https://pre-commit.com/>`__. pre-commit will be installed as part of
the development dependencies specified in requirements.txt. The git
commit hooks can be activated with ``pre-commit install`` inside the
py-eth-index repository.

Initializing the database
-------------------------

Please setup a working postgres environment, i.e. set the PG\*
environment variables and configure ~/.pgpass.

Then run

::

   ethindex createtables

to create the database tables.

ethindex
--------

ethindex is a command line program that is being used to run the actual
syncing process. It also uses the PG\* variables in order to determine
the postgres server to connect to.

ethindex importabi
~~~~~~~~~~~~~~~~~~

Before importing events into the postgres database, the ABIs must be
known.

``ethindex importabi`` can be used to import ABIs into the postgres
database. By default it reads the json file ``addresses.json`` from the current directory
and adds the default abi for currency networks to the abis table.
A custom abi file can be provided via ``--contracts`` option. The location of the
``addresses.json`` file can be specified via the ``--addresses`` command line argument.

Usage:

::

    Usage: ethindex importabi [OPTIONS]

    Options:
      --addresses TEXT
      --contracts TEXT
      --help            Show this message and exit.

ethindex runsync
~~~~~~~~~~~~~~~~

``ethindex runsync`` will start the actual synchronization process. On
the first start it will read all of the abis and create one entry in the
sync table containing all contract addresses. It then imports all of the
events into the postgres table ``events``.

Usage

::

    Usage: ethindex runsync [OPTIONS]

    Options:
      --jsonrpc TEXT                  jsonrpc URL to use
      --required-confirmations INTEGER
                                      number of confirmations until we consider a
                                      block final
      --waittime INTEGER              time to sleep in milliseconds waiting for a
                                      new block
      --startblock INTEGER            Block from where events should be synced
      --syncid TEXT                   syncid to use
      --merge-with-syncid TEXT        syncid to merge with
      --help                          Show this message and exit.

Adding new contracts
--------------------
Import the contracts using the `ethindex importabi` command. Then synchronize
these contracts and merge them with the `default` syncid with something like the
following command::

    ethindex runsync --syncid new --merge-with-syncid default

This command will synchronize all contracts, which aren't already synchronized
for the `default` syncid and will merge the `new` syncid into the `default`
syncid, when both of them are fully synchronized with the chain. This means that
a runsync job has to be running for `default`.


Status and Limitations
----------------------

- ethindex is alpha software.

Change log
----------

See `CHANGELOG <https://github.com/trustlines-protocol/py-eth-index/blob/master/CHANGELOG.rst>`_.

.. |Build Status| image:: https://circleci.com/gh/trustlines-protocol/py-eth-index/tree/master.svg?style=svg
    :target: https://circleci.com/gh/trustlines-protocol/py-eth-index/tree/master
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
