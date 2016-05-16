![taicon](/taicon.png)

# tinkerAccess
Raspberry Pi Access control system

## Using the Server
### Install the Server
The server has been tested on a Rasberry Pi 2 Model B. Installation is very simple.

From the Rasbian terminal:

```
git clone https://github.com/TinkerMill/tinkerAccess.git
cd tinkerAccess
sudo bash
./install.sh
```

#### manage the services

To start/stop/restart the server:
```
service tinkeraccess [start/stop/restart]
```

To stop/start/restart the client:
```
service tinkerclient [start/stop/restart]
```

### Device administration
Due to the fact that incorrectly removing a device can cause big problems, and
that it probably isn't done very much, the functionality to modify devices
is located in the cli program devicemanager.py.  This program will allow
you to add, delete, and rename a device.

#### Add a new device
```sh
cd /opt/tinkeraccess
./devicemanager.py -a -n "front door"
```
#### Delete a device
This will delete the device from the database, and it will also delete
all user access records from the database. (not user accounts, but
the fact they have access to the device you just deleted.)
```sh
cd /opt/tinkeraccess
./devicemanager.py -l
./devicemanager.py -d -i <id_for_front_door>
```
#### Rename a device
```sh
/opt/tinkeraccess
./devicemanager.py -r -i <id_for_device> -n "new name"
```

### User Administration
#### Adding a new user
To add a new user, scan their badge on the card reader.  Once scanned
if the users badge code is not in the database already, the user
will be added to an Inactive Users table.  On the web gui go to:
http://serverip:5000/admin/interface/newuser  and grant access to
the badge you just swiped.
#### Editing a user
once a user exists in the system, you can use the Users tab to modify
what they have access to.  go to http://serverip:5000/admin/interface/user,
select the pencil next to the user you want to edit, and then from there
you can remove or grant access to all the devices currently registered
in the database
