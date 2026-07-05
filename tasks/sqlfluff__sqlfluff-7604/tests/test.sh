#!/bin/bash

cd /app/src

export SQLFLUFF_TESTENV=1

# Copy HEAD test files from /tests (overwrites BASE state)
mkdir -p "test/cli"
cp "/tests/cli/commands_test.py" "test/cli/commands_test.py"
mkdir -p "test/core/rules"
cp "/tests/core/rules/noqa_test.py" "test/core/rules/noqa_test.py"

# Run only the specific test files from this PR
/opt/venv/bin/pytest -xvs \
    test/cli/commands_test.py \
    test/core/rules/noqa_test.py

test_status=$?

if [ $test_status -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
exit "$test_status"
