# tinkerAccess
Raspberry Pi Access control system

## Using the Server
### Device administration
Due to the fact that incorrectly removing a device can cause big problems, and
that it probally isn't done very much, the functionality to modify devices
is located in the cli program devicemanager.py.  This program will allow
you to add, delete, and rename a device.

#### Add a new device
```sh
devicemanager.py -a -n "front door"
```
#### Delete a device
This will delete the device from the database, and it will also delete
all user access records from the database. (not user accounts, but
the fact they have access to the device you just deleted.)
```sh
devicemanager.py -l
devicemanager.py -d -i <id_for_front_door>
```
#### Rename a device
```sh
devicemanager.py -r -i <id_for_device> -n "new name"
```

### User Administration
#### Adding a new user
To add a new user, scan their badge on the card reader.  Once scanned
if the users badge code is not in the database already, the user
will be added to an Invactive Users table.  On the web gui go to:
http://serverip:5000/admin/interface/newuser  and grant access to
the badge you just swiped.
#### Editing a user
once a user exists in the system, you can use the Users tab to modify
what they have access to.  go to http://serverip:5000/admin/interface/user,
select the pencil next to the user you want to edit, and then from there
you can remove or grant access to all the devices currently registered
in the database


## Configuring the server
### configure the test database
    these are the steps for configuring the test database
   - delete db.db from the main directory if it is there
   - run python
   - from the python prompt type:  from serv import init_db
   - then type:  init_db()
### to test the serv.py
	 - as root run python serv.py
	 - connect to http://127.0.0.1:5000/device/0/code/a
	 - that should return json
	 - change the trailing a to ab, and it should return an invalid entry


### getting the environment configured
  -  https://bootstrap.pypa.io/get-pip.py
  -  python get-pip.py
  -  pip install --upgrade pyserial
  -  pip install flask
