# This will build the currently checked out version
#
# we use an intermediate image to build this image. it will make the resulting
# image a bit smaller.
#
# you can build the image with:
#
#   docker build . -t ethindex

FROM ubuntu:18.04 as ubuntu-python
# python needs LANG
ENV LANG C.UTF-8
RUN apt-get -y update \
    && apt-get dist-upgrade -y \
    && apt-get install -y --no-install-recommends python3 libpq5

FROM ubuntu-python as builder
RUN apt-get install -y --no-install-recommends python3-dev python3-venv git build-essential libpq-dev

RUN python3 -m venv /opt/ethindex
RUN /opt/ethindex/bin/pip install --disable-pip-version-check pip==10.0.1

ADD . /py-eth-index

# We need a non-shallow git checkout for setuptools_scm to work. Building with
# something like
#
#   docker build 'https://github.com/trustlines-network/py-eth-index.git#develop' -t ethindex
#
# will only get us a non-shallow git clone. We try to unshallow from the public
# repo with the next command.
RUN sh -c 'cd /py-eth-index; git fetch --tags --unshallow https://github.com/trustlines-network/py-eth-index 2> /dev/null || true'


RUN /opt/ethindex/bin/pip install --disable-pip-version-check -c /py-eth-index/constraints.txt --no-binary=psycopg2 /py-eth-index

# copy the contents of the virtualenv from the intermediate container
FROM ubuntu-python
RUN rm -rf /var/lib/apt/lists/*
WORKDIR /opt/ethindex
COPY --from=builder /opt/ethindex /opt/ethindex
RUN ln -s /opt/ethindex/bin/ethindex /usr/local/bin/
CMD ["/opt/ethindex/bin/ethindex"]
