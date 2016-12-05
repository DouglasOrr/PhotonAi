docker run --rm -it \
       -v `pwd`:/local -v /var/run/docker.sock:/var/run/docker.sock \
       -w /local -e HOST_ROOT=`pwd` \
       douglasorr/photonai photonai run $@
