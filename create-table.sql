-- psql -f create-table.sql
CREATE TABLE events (
  transactionHash text NOT NULL,
  blockNumber integer NOT NULL,
  address text NOT NULL,
  eventName text NOT NULL,
  args jsonb,
  blockHash text NOT NULL,
  transactionIndex integer NOT NULL,
  logIndex integer NOT NULL,
  timestamp integer NOT NULL,
  PRIMARY KEY(transactionHash, address, blockHash, transactionIndex, logIndex)
);

CREATE TABLE sync (
       syncid text NOT NULL PRIMARY KEY,
       last_block_number integer NOT NULL,
       last_block_hash text NOT NULL,
       addresses text[] NOT NULL
);

CREATE TABLE abis (
       contract_address text NOT NULL PRIMARY KEY,
       abi jsonb NOT NULL
);
