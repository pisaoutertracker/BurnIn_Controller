podman run --name forController  -d -ti  -v  /home/thermal/Ph2_ACF_docker/:/home/thermal/Ph2_ACF_docker/ -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct  -v /home/thermal/suvankar/power_supply/:/home/thermal/suvankar/power_supply/ --net host -w $PWD gitlab-registry.cern.ch/cms_tk_ph2/docker_exploration/cmstkph2_user_c7:ph2_acf_v4-16 

#podman run -d --name forController --rm -ti -v $PWD:$PWD -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct  -v /home/thermal/suvankar/power_supply/:/home/thermal/suvankar/power_supply/ --net host -w $PWD gitlab-registry.cern.ch/cms_tk_ph2/docker_exploration/cmstkph2_user_c7:ph2_acf_v4-16

# to delete the container : podman stop forController && podman rm forController
