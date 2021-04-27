==========
Change Log
==========
`unreleased`_
---------------------

`0.4.1`_ (2021-04-27)
---------------------
- By default, direclty load abi from `tlbin` package on command `ethindex importabi`
  you can still provide option `--contracts <path>` to use custom abi
- Command `ethindex importabi` now erases the old abi if an abi for an address was already imported.
  This allows to rerun the command to update abi without having to drop the table.

`0.4.0`_ (2021-03-04)
---------------------
- Changed: updated to be comatible with python 3.8 and 3.9

- Removed: no longer support python < 3.8

`0.3.5`_ (2021-02-10)
---------------------
- Changed: no longer raiser RuntimeError when receiving an event of unknown abi but log a warning.
  This is useful for proxied contracts that may emit events related to the proxy administration.
- Changed: createtable will warn if table already exists instead of crashing.
  This allow to upgrade ethindex from versions where the graphfeed table did not exist to ones where it does.
- Changed: load abi from `CurrencyNetworkOwnable` instead of `CurrencyNetwork` to have abi about
  `NetworkUnfreeze` event

- Added: Update the `graphfeed` table with information about network frozen status.
  The updates have name `NetworkFreeze` or `NetworkUnfreeze`.

`0.3.4`_ (2020-12-18)
---------------------
- Use events from database to figure out sent events to relay instead of memory.
  That makese graph sync feature safe on restart of the indexer

`0.3.3`_ (2020-12-14)
---------------------
- Add table `graphfeed` populated with graph updates for the relay to sync its graph with


`0.3.2`_ (2020-02-14)
---------------------
- Switch to a src based layout
- Update all dependencies

`0.3.1`_ (2019-04-03)
---------------------
- transfer copyright to trustlines foundation
- run end2end tests on circleci

`0.3.0`_ (2019-01-14)
---------------------
- `ethindex --version` will now print the current version of ethindex.
- `ethindex` has been set as entrypoint in the docker executable. Beware, this
  is a breaking change.

`0.2.1`_ (2019-01-03)
-----------------------
* reduce log output when fully synced

`0.2.0`_ (2018-09-07)
-----------------------
* ethindex handles chain reorgs
* the database schema has been changed. Please rebuild your database
* new contracts can now be added

`0.1.1`_ (2018-08-21)
-----------------------
* eth-index has been released on PyPI
* basic test infrastructure has been added


.. _0.1.1: https://github.com/trustlines-protocol/py-eth-index/compare/0.1.0...0.1.1
.. _0.2.0: https://github.com/trustlines-protocol/py-eth-index/compare/0.1.1...0.2.0
.. _0.2.1: https://github.com/trustlines-protocol/py-eth-index/compare/0.2.0...0.2.1
.. _0.3.0: https://github.com/trustlines-protocol/py-eth-index/compare/0.2.1...0.3.0
.. _0.3.1: https://github.com/trustlines-protocol/py-eth-index/compare/0.3.0...0.3.1
.. _0.3.2: https://github.com/trustlines-protocol/py-eth-index/compare/0.3.1...0.3.2
.. _0.3.3: https://github.com/trustlines-protocol/py-eth-index/compare/0.3.2...0.3.3
.. _0.3.4: https://github.com/trustlines-protocol/py-eth-index/compare/0.3.3...0.3.4
.. _0.3.5: https://github.com/trustlines-protocol/py-eth-index/compare/0.3.4...0.3.5
.. _0.4.0: https://github.com/trustlines-protocol/py-eth-index/compare/0.3.5...0.4.0
.. _0.4.1: https://github.com/trustlines-protocol/py-eth-index/compare/0.4.0...0.4.1
.. _unreleased: https://github.com/trustlines-protocol/py-eth-index/compare/0.4.1...master
