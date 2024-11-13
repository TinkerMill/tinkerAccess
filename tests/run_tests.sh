#!/bin/bash
set -e

# Run the unit tests
python -m pytest tests/test_server.py -v

# Exit with the pytest exit code
exit $?
