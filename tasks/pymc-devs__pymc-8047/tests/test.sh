#!/bin/bash

cd /app/src

export CI=true

# Copy HEAD test files from /tests (overwrites BASE state)
mkdir -p "tests/progress_bar"
cp "/tests/progress_bar/test_manager.py" "tests/progress_bar/test_manager.py"
mkdir -p "tests/progress_bar"
cp "/tests/progress_bar/test_marimo.py" "tests/progress_bar/test_marimo.py"
mkdir -p "tests/smc"
cp "/tests/smc/test_smc.py" "tests/smc/test_smc.py"

# Run ONLY the specific test files from the PR
/opt/venv/bin/pytest -xvs tests/progress_bar/test_manager.py tests/progress_bar/test_marimo.py tests/smc/test_smc.py
test_status=$?

if [ $test_status -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
exit "$test_status"
