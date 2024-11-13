-- Test data for API tests
INSERT INTO device (id, name, allUsers, lockout, lockout_start, lockout_end) 
VALUES (1, 'Test Device', 0, 0, '12:00 AM', '12:00 AM');

INSERT INTO user (id, name, code, status) 
VALUES 
(1, 'Test User', '123456', 'A'),
(2, 'Admin User', 'admin123', 'S');

INSERT INTO deviceAccess (user, device, time, trainer)
VALUES (1, 1, 100, 0);

INSERT INTO newuser (id, code, deviceID)
VALUES
('3', '234567', '1');
