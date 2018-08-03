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
    && apt-get install -y --no-install-recommends python3 python3-distutils libpq5

FROM ubuntu-python as builder
RUN apt-get install -y --no-install-recommends python3-dev python3-venv git build-essential libpq-dev

RUN python3 -m venv /opt/ethindex
WORKDIR /opt/ethindex
RUN bin/pip install --disable-pip-version-check pip==18.0

COPY ./constraints.txt /py-eth-index/constraints.txt
COPY ./requirements.txt /py-eth-index/requirements.txt
# remove development dependencies from the end of the file
RUN sed -i -e '/development dependencies/q' /py-eth-index/requirements.txt

RUN bin/pip install --disable-pip-version-check -c /py-eth-index/constraints.txt -r /py-eth-index/requirements.txt

COPY . /py-eth-index
RUN bin/pip install --disable-pip-version-check -c /py-eth-index/constraints.txt --no-binary=psycopg2 /py-eth-index
RUN bin/python -c 'import pkg_resources; print(pkg_resources.get_distribution("eth-index").version)' >VERSION

# copy the contents of the virtualenv from the intermediate container
FROM ubuntu-python
RUN rm -rf /var/lib/apt/lists/*
WORKDIR /opt/ethindex
COPY --from=builder /opt/ethindex /opt/ethindex
RUN ln -s /opt/ethindex/bin/ethindex /usr/local/bin/
CMD ["/opt/ethindex/bin/ethindex"]
