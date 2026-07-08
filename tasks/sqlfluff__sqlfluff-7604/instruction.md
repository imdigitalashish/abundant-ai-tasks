`sqlfluff parse` does not currently respect inline `noqa` directives for parsing and templating violations, even though `sqlfluff lint` does.

When parsing SQL that triggers a parse error (rule code `PRS`) or templating error (rule code `TMP`), an inline `-- noqa` comment on the offending line should suppress that reported violation. Instead, `sqlfluff parse` reports the raw violations without applying the ignore mask, so users still see `PRS`/`TMP` failures that should be ignored.

Reproduction example (MariaDB dialect):

```sql
INSERT INTO transaction (
    id,
    amount,
    transaction_status
)
VALUES (
    :id,
    :amount,
    :transaction_status
)
ON DUPLICATE KEY UPDATE
amount = VALUES (amount),
transaction_status = IF(transaction_status = 'CONFIRMED', transaction_status, VALUES (transaction_status)) -- noqa
```

Running `sqlfluff parse` (with dialect `mariadb` and templater `placeholder`) currently emits a parsing violation like:

```
L:  12 | P:  25 |  PRS | Line 12, Position 25: Found unparsable section: ',\ntransaction_status = IF(transaction_st...'
WARNING: Parsing errors found and dialect is set to 'mariadb'. Have you configured your dialect correctly?
```

Expected behavior:
- With an inline `-- noqa` on the line that triggers the parse/templating violation, `sqlfluff parse` should suppress the corresponding `PRS`/`TMP` violation output (i.e., it should apply the same ignore/noqa handling behavior as linting).
- If the user runs `sqlfluff parse --disable-noqa ...`, inline `noqa` directives must be ignored and the `PRS`/`TMP` violation should be reported again.

Implement the fix so that the `parse` command filters parse and templating violations through the existing noqa/ignore-mask logic (including honoring `NoQaDirective` parsing and `IgnoreMask` application), matching the behavior users already get from `Linter`-based linting output.