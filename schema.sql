-- from serv import init_db
-- init_db()

CREATE TABLE user(id INTEGER PRIMARY KEY, name TEXT, code TEXT);
CREATE TABLE device(id INTEGER PRIMARY KEY, name TEXT, allUsers BOOLEAN);
CREATE TABLE deviceAccess(id INTEGER PRIMARY KEY, user INTEGER, device INTEGER, time INTEGER, trainer BOOLEAN);
create table newuser(id INTEGER PRIMARY KEY, code TEXT, deviceID INTEGER);
create table log(id INTEGER PRIMARY KEY, message TEXT, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);

insert into device (id, name, allUsers) values (0, 'laser cutter', 0);
insert into device (id, name, allUsers) values (1, '3d printer', 0);

insert into user (id, name, code) values (1, 'ron', '150060E726B4');
insert into user (id, name, code) values (2, 'test', 'a');

insert into deviceAccess (id, user, device, time) values ( 1, 2, 0, 100);

insert into newuser (id, code, deviceID) values (0, 'bbb', 0);
