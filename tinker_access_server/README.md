# tinker-access-server
All the commands below should be executed from the terminal on the relevant TinkerAccess server.

#### Manage the Services

To start/stop/restart the server:
```
sudo service tinkerserver [start/stop/restart]
```

To stop/start/restart the client:
```
sudo service tinkerclient [start/stop/restart]
```

### Device administration
Incorrectly removing a device can cause big problems and
is rarely needed, so the functionality to modify devices
is located in the cli program devicemanager.py.  This program will allow
you to add, delete, and rename a device.

#### Add a new device 
```
cd /opt/tinkeraccess
sudo ./devicemanager.py -a -n "<new device name>"
```
#### Delete a device
This will delete the device from the database, and it will also delete
all user access records from the database. (not user accounts, but
the fact they have access to the device you just deleted.)
```
cd /opt/tinkeraccess
./devicemanager.py -l
sudo ./devicemanager.py -d -i <device ID to be deleted>
```
#### Rename a device
```
cd /opt/tinkeraccess
sudo ./devicemanager.py -r -i <device ID for name change> -n "<new device name>"
```
#### Grant all users access to a device
This command will grant all users access to the device. Any user in the database will be authenicated to use the device. This command
sets the all users column of the device table
```
cd /opt/tinkeraccess
./devicemanager.py -l
sudo ./devicemanager.py -u -i <device ID to grant all user access>
```
#### Remove all users access to a device
This command sets up the device access level on a per user basis. Users will need to be specifically granted access to be authenicated to use the device. This command
clears the all users column of the device table
```
cd /opt/tinkeraccess
./devicemanager.py -l
sudo ./devicemanager.py -c -i <device ID to remove all user access>
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
