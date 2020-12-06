#!/usr/bin/env bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

sqlite3 /opt/tinkeraccess/db.db "ALTER TABLE device ADD COLUMN allUsers BOOLEAN DEFAULT(0)"
