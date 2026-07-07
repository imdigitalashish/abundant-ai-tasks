#!/bin/bash

cd /app/src

export CI=true

# Copy HEAD test files from /tests (overwrites BASE state)
mkdir -p "test/fixtures/dialects/tsql"
cp "/tests/fixtures/dialects/tsql/data_types.sql" "test/fixtures/dialects/tsql/data_types.sql"
mkdir -p "test/fixtures/dialects/tsql"
cp "/tests/fixtures/dialects/tsql/data_types.yml" "test/fixtures/dialects/tsql/data_types.yml"
mkdir -p "test/fixtures/dialects/tsql"
cp "/tests/fixtures/dialects/tsql/datatype_methods.sql" "test/fixtures/dialects/tsql/datatype_methods.sql"
mkdir -p "test/fixtures/dialects/tsql"
cp "/tests/fixtures/dialects/tsql/datatype_methods.yml" "test/fixtures/dialects/tsql/datatype_methods.yml"
mkdir -p "test/fixtures/dialects/tsql"
cp "/tests/fixtures/dialects/tsql/xml_schema_collection.sql" "test/fixtures/dialects/tsql/xml_schema_collection.sql"
mkdir -p "test/fixtures/dialects/tsql"
cp "/tests/fixtures/dialects/tsql/xml_schema_collection.yml" "test/fixtures/dialects/tsql/xml_schema_collection.yml"

# CRITICAL: Run ONLY the tests exercising the new/changed fixtures from this PR.
# dialects_test.py discovers every file under test/fixtures/dialects/ and
# parametrizes on (dialect, filename), so we select the relevant fixtures by
# name via -k rather than running the whole dialect matrix.
pytest -v test/dialects/dialects_test.py \
  -k "data_types or datatype_methods or xml_schema_collection"
test_status=$?

if [ $test_status -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
exit "$test_status"
