#!/bin/bash

kill_server() {
     pkill python
     pkill sleep
}
trap 'kill_server' SIGINT

# Initialize test database

# Start the server
python /app/server.py & 

echo -n "Waiting for server to start."
until curl -s http://127.0.0.1:5000 > /dev/null; do echo -n "."; sleep 1; done


# Run all tests
if [ -z $1 ]; then 
    hurl --variables-file tests/api/setup.hurl \
         --variable ADMIN_PASSWORD=testpassword \
         --variable BASE_URL=http://127.0.0.1:5000 \
         --test \
        tests/api/device_tests.hurl \
        tests/api/admin_tests.hurl \
        tests/api/tool_summary_tests.hurl \
        tests/api/root_tests.hurl \
        tests/api/login_tests.hurl
else
    sleep infinity
fi
