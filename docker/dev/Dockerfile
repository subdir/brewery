FROM python:3.5

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        curl \
        gcc \
        make \
        libc6-dev \
        libusb-dev \
        libusb++-dev \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN set -x \
    && mkdir /usr/src/phidget \
    && cd /usr/src/phidget \
    && curl \
        'http://www.phidgets.com/downloads/libraries/libphidget_2.1.8.20150410.tar.gz' \
        -o libphidget.tar.gz \
    && tar --strip-components=1 -xz -f libphidget.tar.gz \
    && ./configure \
    && make install \
    && rm -rf /usr/src/phidget

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        runit \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pylint
RUN pip3 install pytest

