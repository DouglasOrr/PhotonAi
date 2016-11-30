FROM python:3

# Setup node (just so we can use browserify... eugh!)
RUN apt-get update \
    && apt-get install -y npm \
    && apt-get clean \
    && ln -s /usr/bin/nodejs /usr/bin/node \
    && npm install -g browserify

COPY . /tmp/app

# Install the dependencies & a copy of the app
RUN cd /tmp/app                                       \
    && ./scripts/build-web			      \
    && pip install --no-cache-dir -r requirements.txt \
    && python setup.py install                        \
    && rm -r /tmp/app
