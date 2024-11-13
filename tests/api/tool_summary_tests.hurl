# Test tool summary with default dates
GET {{BASE_URL}}/toolSummary
HTTP 200
[Asserts]
header "Content-Type" contains "text/html"

# Test tool summary with custom start date
GET {{BASE_URL}}/toolSummary/2023-01-01
HTTP 200
[Asserts]
header "Content-Type" contains "text/html"

# Test tool summary with custom start and end dates
GET {{BASE_URL}}/toolSummary/2023-01-01/2023-12-31
HTTP 200
[Asserts]
header "Content-Type" contains "text/html"
