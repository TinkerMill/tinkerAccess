#!/usr/bin/env bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

sqlite3 /opt/tinkeraccess/db.db "ALTER TABLE device ADD COLUMN lockout INTEGER DEFAULT(0)"
sqlite3 /opt/tinkeraccess/db.db "ALTER TABLE device ADD COLUMN lockout_start TEXT DEFAULT('12:00 AM')"
sqlite3 /opt/tinkeraccess/db.db "ALTER TABLE device ADD COLUMN lockout_end TEXT DEFAULT('12:00 AM')"
