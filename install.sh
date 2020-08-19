#!/usr/bin/env bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

dir="/opt/tinkeraccess"

apt update
apt install python-pip python-setuptools
pip install flask

if [ ! -f /usr/bin/sqlite3 ] ; then
   apt update
   apt install sqlite3
fi

# if the directory doesn't exist create it
if [ ! -d $dir ] ; then
   mkdir -p $dir
fi

# if the database doesn't exist create it
if [ ! -f $dir/db.db ] ; then
   sqlite3 $dir/db.db < schema.sql
fi

# copy over the files we need
cp server.py $dir
cp example_server.cfg $dir/server.cfg
chmod 755 $dir/server.py
cp -r static $dir
cp -r templates $dir
cp devicemanager.py $dir

# install the Server startup service
cp scripts/tinkerserver /etc/init.d
chmod 755 /etc/init.d/tinkerserver
update-rc.d tinkerserver defaults 91
service tinkerserver restart

# install the Client startup service
pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir tinker-access-client --no-binary tinker-access-client
cp tinker_access_client/config_file/tinker-access-client.conf /etc

echo ""
echo "The ${dir}/server.cfg file needs to be edited for the server setup before restarting"
echo "The /etc/tinker-access-client.conf file needs to be edited for the client setup before restarting"
echo ""
