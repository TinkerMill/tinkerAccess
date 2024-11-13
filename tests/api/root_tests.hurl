# Test root endpoint
GET {{BASE_URL}}/
HTTP 200
[Asserts]
header "Content-Type" contains "text/html"
