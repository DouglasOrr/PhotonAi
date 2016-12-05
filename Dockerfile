FROM photonai-dev

# Install a copy of the app
COPY . /tmp/app
RUN cd /tmp/app                                        \
    && ./scripts/build-web			       \
    && python3 setup.py install                        \
    && rm -r /tmp/app
