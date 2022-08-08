-- from serv import init_db
-- init_db()

CREATE TABLE user(id INTEGER PRIMARY KEY, name TEXT, code TEXT, status CHARACTER(1) DEFAULT('A'));
CREATE TABLE device(id INTEGER PRIMARY KEY, name TEXT, allUsers BOOLEAN, lockout INTEGER DEFAULT(0), lockout_start TEXT DEFAULT('12:00 AM'), lockout_end TEXT DEFAULT('12:00 AM'));
CREATE TABLE deviceAccess(id INTEGER PRIMARY KEY, user INTEGER, device INTEGER, time INTEGER, trainer BOOLEAN);
create table newuser(id INTEGER PRIMARY KEY, code TEXT, deviceID INTEGER);
create table log(id INTEGER PRIMARY KEY, message TEXT, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);

insert into device (id, name, allUsers) values (0, 'laser cutter', 0);
insert into device (id, name, allUsers) values (1, '3d printer', 0);

insert into user (id, name, code, status) values (1, 'ron', '150060E726B4', 'A');
insert into user (id, name, code, status) values (2, 'test', 'a', 'I');

insert into deviceAccess (id, user, device, time) values ( 1, 2, 0, 100);

insert into newuser (id, code, deviceID) values (0, 'bbb', 0);
