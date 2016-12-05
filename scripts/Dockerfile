FROM ubuntu:16.04

# Docker prerequisites
RUN apt-get update                                            \
    && apt-get upgrade -y                                     \
    && apt-get install -y apt-transport-https ca-certificates \
    && apt-key adv                                            \
        --keyserver hkp://ha.pool.sks-keyservers.net:80       \
        --recv-keys 58118E89F3A912897C070ADBF76221572C52609D  \
    && echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" \
    > /etc/apt/sources.list.d/docker.list

# (Setup node just so we can use browserify... eugh!)
RUN apt-get update                         \
    && apt-get install -y                  \
       docker-engine                       \
       npm                                 \
       python3                             \
       python3-pip                         \
    && apt-get clean                       \
    && ln -s /usr/bin/nodejs /usr/bin/node \
    && npm install -g browserify

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# Install the dependencies
COPY requirements.txt /tmp/app/requirements.txt
RUN cd /tmp/app                                        \
    && pip3 install --no-cache-dir -r requirements.txt \
    && rm -r /tmp/app
