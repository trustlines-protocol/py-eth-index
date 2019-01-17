#! /bin/bash

set -x
set -u

# source .env in case we have the environment variables set locally
source .env

docker-compose up --no-start
docker-compose up helper
docker cp config.json e2e-helper:/shared
docker cp parity-dev-pw e2e-helper:/shared
docker-compose up -d postgres parity

sleep 5
docker-compose up contracts
docker-compose up createtables
docker-compose up init
docker-compose up -d index relay
sleep 3
docker-compose up -d e2e
docker-compose logs -t -f parity index relay e2e &
result=$(docker wait e2e)
mydir=$(mktemp -td end2end.XXXXXX)
docker-compose logs -t e2e >$mydir/output.txt
docker-compose down -v
cat $mydir/output.txt
echo rm -r $mydir
exit $result
