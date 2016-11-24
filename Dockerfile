FROM python:3

COPY . /tmp/app

# Install a the dependencies & a copy of the app
RUN cd /tmp/app                                       \
    && pip install --no-cache-dir -r requirements.txt \
    && python setup.py install                        \
    && rm -r /tmp/app
