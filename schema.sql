-- from server import init_db
-- init_db()

CREATE TABLE user(id INTEGER PRIMARY KEY, name TEXT, code TEXT);
CREATE TABLE device(id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE deviceAccess(id INTEGER PRIMARY KEY, user INTEGER, device INTEGER, time INTEGER);

insert into device (id, name) values (0, 'laser cutter');
insert into device (id, name) values (1, '3d printer');

insert into user (id, name, code) values (1, 'ron', '150060E726B4');
insert into user (id, name, code) values (2, 'test', 'a');

insert into deviceAccess (id, user, device, time) values ( 1, 2, 0, 100); 

