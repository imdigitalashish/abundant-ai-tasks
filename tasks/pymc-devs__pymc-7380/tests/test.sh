#!/bin/bash

cd /app/src

export CI=true

# Copy HEAD test files from /tests (overwrites BASE state)
mkdir -p "tests/distributions"
cp "/tests/distributions/test_multivariate.py" "tests/distributions/test_multivariate.py"
mkdir -p "tests/distributions"
cp "/tests/distributions/test_transform.py" "tests/distributions/test_transform.py"
mkdir -p "tests/sampling"
cp "/tests/sampling/test_jax.py" "tests/sampling/test_jax.py"

# Run ONLY the specific test files from the PR, NOT the entire test suite!
/opt/venv/bin/pytest -v \
    tests/distributions/test_multivariate.py \
    tests/distributions/test_transform.py \
    tests/sampling/test_jax.py
test_status=$?

if [ $test_status -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
exit "$test_status"
