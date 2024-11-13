-- from serv import init_db
-- init_db()

CREATE TABLE user(id INTEGER PRIMARY KEY, name TEXT, code TEXT, status CHARACTER(1) DEFAULT('A'));
CREATE TABLE device(id INTEGER PRIMARY KEY, name TEXT, allUsers BOOLEAN, lockout INTEGER DEFAULT(0), lockout_start TEXT DEFAULT('12:00 AM'), lockout_end TEXT DEFAULT('12:00 AM'));
CREATE TABLE deviceAccess(id INTEGER PRIMARY KEY, user INTEGER, device INTEGER, time INTEGER, trainer BOOLEAN);
create table newuser(id INTEGER PRIMARY KEY, code TEXT, deviceID INTEGER);
create table log(id INTEGER PRIMARY KEY, message TEXT, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);

