# Photonai

A simulator for an [AI challenge](http://photonai.cloudapp.net).

## Run locally

Install [Docker](https://docs.docker.com/engine/installation/linux/ubuntulinux/).

Copy [run.sh](run.sh) and make executable (`chmod +x run.sh`).

Download [examples/spiral.py](examples/spiral.py) and run your first bot:

    ./run.sh -b examples/spiral.py -o eg.jsonl

[Vizualize](http://photonai.cloudapp.net/player) the replay.

Read [documentation](http://photonai.cloudapp.net/doc/photonai/index.html) and design
your bot.

## Tournament

Submit bots to our [server](http://photonai.cloudapp.net/uploader).

N.B. Our tournament is being run with the following game configuration (which can be
passed as config.yaml to `./run.sh -c config.yaml`).

    time_limit: 60
    step_duration: 0.01
    timeout: 0.1
    maps:
      - empty
      - singleton
      - orbital
      - binary
