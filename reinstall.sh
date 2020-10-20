#!/usr/bin/env bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

dir="/opt/tinkeraccess"

# if the directory doesn't exist create it
if [ ! -d $dir ] ; then
	echo "Target directory doesn't exist: $dir"
	echo "	if this is a new installation, use install.sh"
	exit
fi

# copy over the files we need
cp server.py $dir
chmod 755 $dir/server.py
cp -r static $dir
cp -r templates $dir
cp devicemanager.py $dir

# install the Server startup service
service tinkerserver stop
cp scripts/tinkerserver /etc/init.d
chmod 755 /etc/init.d/tinkerserver
update-rc.d tinkerserver defaults 91
service tinkerserver start

# install the Client startup service
pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir tinker-access-client --no-binary tinker-access-client
