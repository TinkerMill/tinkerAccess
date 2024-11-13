# Test valid login
GET {{BASE_URL}}/checkLogin/admin/{{ADMIN_PASSWORD}}
HTTP 200
[Asserts]
body == "true"

# Test invalid login
GET {{BASE_URL}}/checkLogin/admin/wrongpassword
HTTP 200
[Asserts]
body == "false"
