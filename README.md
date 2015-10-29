# tinkerAccess
Raspberry Pi Access control system

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
