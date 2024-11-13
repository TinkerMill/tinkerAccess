# Set admin password cookie
# SET ADMIN_PASSWORD=testpassword

# Test admin interface endpoints
GET {{BASE_URL}}/admin/interface/user
Cookie: password={{ADMIN_PASSWORD}}
HTTP 200
[Asserts]
header "Content-Type" contains "text/html"

GET {{BASE_URL}}/admin/interface/devices
Cookie: password={{ADMIN_PASSWORD}}
HTTP 200
[Asserts]
header "Content-Type" contains "text/html"

GET {{BASE_URL}}/admin/interface/newuser
Cookie: password={{ADMIN_PASSWORD}}
HTTP 200
[Asserts]
header "Content-Type" contains "text/html"

# Test admin user management endpoints
GET {{BASE_URL}}/admin/addUser/3/name/NewUser
Cookie: password={{ADMIN_PASSWORD}}
HTTP 302
[Asserts]
header "Location" contains "/admin/interface/user"

GET {{BASE_URL}}/admin/activateUser/3
Cookie: password={{ADMIN_PASSWORD}}
HTTP 302
[Asserts]
header "Location" contains "/admin/interface/inactiveuser"

GET {{BASE_URL}}/admin/deactivateUser/3
Cookie: password={{ADMIN_PASSWORD}}
HTTP 302
[Asserts]
header "Location" contains "/admin/interface/user"

GET {{BASE_URL}}/admin/delUser/3
Cookie: password={{ADMIN_PASSWORD}}
HTTP 302
[Asserts]
header "Location" contains "/admin/interface/inactiveuser"

# Test admin device management endpoints
GET {{BASE_URL}}/admin/deviceUnlimitedHr/1
Cookie: password={{ADMIN_PASSWORD}}
HTTP 302
[Asserts]
header "Location" contains "/admin/interface/devices"

GET {{BASE_URL}}/admin/deviceLimitedHr/1
Cookie: password={{ADMIN_PASSWORD}}
HTTP 302
[Asserts]
header "Location" contains "/admin/interface/devices"

GET {{BASE_URL}}/admin/deviceLockout/1
Cookie: password={{ADMIN_PASSWORD}}
HTTP 302
[Asserts]
header "Location" contains "/admin/interface/devices"

# Test unauthorized access
GET {{BASE_URL}}/admin/interface/user
HTTP 302
[Asserts]
header "Location" == "{{BASE_URL}}/"
