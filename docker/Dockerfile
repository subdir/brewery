FROM python:3.5

# Зависимости для phidget
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        curl \
        gcc \
        make \
        libc6-dev \
        libusb-dev \
        libusb++-dev \
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

# Зависимости для phidget-python
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN set -x \
    && mkdir /usr/src/phidget-python \
    && cd /usr/src/phidget-python \
    && git clone 'https://github.com/subdir/phidgets-python3.git' \
    && cd phidgets-python3/PhidgetsPython \
    && python3 setup.py install \
    && rm -rf /usr/src/phidget-python

# Средства разработки
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        mc \
        vim \
    && rm -rf /var/lib/apt/lists/*

