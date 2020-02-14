# This will build the currently checked out version
#
# we use an intermediate image to build this image. it will make the resulting
# image a bit smaller.
#
# you can build the image with:
#
#   docker build . -t ethindex

FROM ubuntu:18.04 as builder
# python needs LANG
ENV LANG C.UTF-8
RUN apt-get -y update \
&& apt-get install -y --no-install-recommends python3 python3-distutils libpq5 \
               python3-dev python3-venv git build-essential libpq-dev

RUN python3 -m venv /opt/ethindex
ENV PATH "/opt/ethindex/bin:${PATH}"

WORKDIR /py-eth-index

COPY ./constraints.txt constraints.txt
RUN pip install -c constraints.txt --disable-pip-version-check pip wheel setuptools

COPY ./requirements.txt requirements.txt
# remove development dependencies from the end of the file
RUN sed -i -e '/development dependencies/q' requirements.txt

COPY . /py-eth-index
RUN pip install --disable-pip-version-check -c constraints.txt .
RUN python -c 'import importlib_metadata; print(importlib_metadata.version("eth-index"))' >/opt/ethindex/VERSION

# copy the contents of the virtualenv from the intermediate container
FROM ubuntu:18.04 as runner
ENV LANG C.UTF-8
RUN apt-get -y update \
    && apt-get install -y --no-install-recommends python3 python3-distutils libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /opt/ethindex/bin/ethindex /usr/local/bin/

FROM runner
COPY --from=builder /opt/ethindex /opt/ethindex
WORKDIR /opt/ethindex
ENTRYPOINT ["/opt/ethindex/bin/ethindex"]
