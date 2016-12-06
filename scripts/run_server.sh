docker kill photonai-server
docker rm photonai-server
# Note this dance with /etc/hosts
# - http://werkzeug.pocoo.org/docs/0.11/serving/#troubleshooting
# - https://github.com/docker/docker/issues/22281
docker run -d --name photonai-server -v /replays:/replays -v `pwd`/config.yaml:/config.yaml -p 80:80 douglasorr/photonai \
       bash -c 'sed "s/::1/# ::1/" /etc/hosts > /tmp/hosts && cat /tmp/hosts > /etc/hosts && photonai server -c /config.yaml'
