# Test device login endpoint
GET {{BASE_URL}}/device/1/code/123456
HTTP 200
[Asserts]
jsonpath "$.devicename" exists
jsonpath "$.username" exists
jsonpath "$.userid" exists
jsonpath "$.time" exists
jsonpath "$.devicename" == "Test Device"
jsonpath "$.username" == "Test User"
jsonpath "$.userid" == 1
jsonpath "$.time" == 100

# Test device login with invalid code
GET {{BASE_URL}}/device/1/code/invalid
HTTP 200
[Asserts]
jsonpath "$.devicename" == "none"
jsonpath "$.username" == "none"
jsonpath "$.userid" == -1
jsonpath "$.time" == 0

# Test device login with invalid device
GET {{BASE_URL}}/device/999/code/123456
HTTP 200
[Asserts]
jsonpath "$.devicename" == "none"
jsonpath "$.username" == "none"
jsonpath "$.userid" == -1
jsonpath "$.time" == 0

# Test device logout endpoint
GET {{BASE_URL}}/device/1/logout/1
HTTP 200
[Asserts]
body == ""
