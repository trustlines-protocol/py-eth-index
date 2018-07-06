# This will build the currently checked out version
#
# we use an intermediate image to build this image. it will make the resulting
# image a bit smaller.
#
# you can build the image with:
#
#   docker build . -t ethindex

FROM python:3.6.5-stretch as intermediate

RUN python3 -m venv /opt/ethindex
RUN /opt/ethindex/bin/pip install --disable-pip-version-check pip==10.0.1

ADD . /py-eth-index
RUN /opt/ethindex/bin/pip install --disable-pip-version-check -c /py-eth-index/constraints.txt --no-binary=psycopg2 /py-eth-index

# copy the contents of the virtualenv from the intermediate container
FROM python:3.6.5-stretch
WORKDIR /opt/ethindex
COPY --from=intermediate /opt/ethindex /opt/ethindex
CMD ["/opt/ethindex/bin/ethindex"]
