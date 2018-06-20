-- psql -f create-table.sql
CREATE TABLE events (
  transactionHash text NOT NULL,
  blockNumber integer NOT NULL,
  address text NOT NULL,
  eventName text NOT NULL,
  args jsonb,
  blockHash text NOT NULL,
  transactionIndex integer NOT NULL,
  logIndex integer NOT NULL
);
