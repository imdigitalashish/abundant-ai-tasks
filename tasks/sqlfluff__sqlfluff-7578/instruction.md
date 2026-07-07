SQLFluff’s TSQL dialect parser currently fails to parse several valid T-SQL constructs related to XML schema collections, typed XML, and datatype “method” calls. This manifests as parser warnings/errors (e.g., SQLFluff(PRS)) when linting or parsing statements that are valid in SQL Server.

The parser must be updated so that these statements parse successfully in the TSQL dialect:

1) XML schema collection DDL
The dialect should recognize and parse the following statement forms:
- `CREATE XML SCHEMA COLLECTION <schema_collection_name> AS <xml_schema_definition>`
  where `<xml_schema_definition>` can be an `N'...'` string literal or a variable containing the schema text.
- `ALTER XML SCHEMA COLLECTION <schema_collection_name> ADD <xml_schema_definition>`
  where `<xml_schema_definition>` can be a string literal or a variable.
- `DROP XML SCHEMA COLLECTION <schema_collection_name>`

`<schema_collection_name>` should support multipart identifiers (e.g., `dbo.SomeXmlSchemaCollection`). Statements may appear in scripts with batch separators like `GO`.

2) Typed XML declarations
The dialect should parse typed XML declarations, including schema-qualified and bracketed identifiers, and the optional `DOCUMENT` keyword:
- `DECLARE @typed_xml XML (SomeSchemaCollection);`
- `DECLARE @typed_xml XML (dbo.SomeSchemaCollection);`
- `DECLARE @typed_xml XML ([dbo].[SomeSchemaCollection]);`
- `DECLARE @typed_xml_document XML (DOCUMENT dbo.SomeSchemaCollection);`
These should be treated as valid uses of the `XML` data type with a parenthesized schema collection reference.

3) Datatype method calls on expressions (XML, hierarchyid, spatial)
The dialect should parse method-call syntax that appears as a dotted suffix on an expression, including when chained, and regardless of whether the left-hand side is a variable, column, function call, or a parenthesized subquery expression:
- XML examples:
  - `SELECT @XML.value('.', 'nvarchar(max)');`
  - `SELECT CONVERT(xml, N'<r></r>').value('.','nvarchar(max)');`
  - `SELECT (SELECT CONVERT(xml, N'<r></r>')).value('.','nvarchar(max)');`
  - `SELECT @xml.query('.').query('.');` (chained)
- hierarchyid examples:
  - `SELECT @hierarchyid.GetAncestor(2);`
  - `SELECT convert(hierarchyid, '/1/1/2').GetAncestor(2).GetAncestor(2);` (chained)
- spatial examples:
  - `SELECT @geometry.STEndPoint();`
  - `SELECT @geography.STArea();`
  - `SELECT @geography.STDistance(@other_geography);`

A key requirement is that method names should be treated as case-sensitive tokens in the sense that SQLFluff must not normalize/auto-fix their casing as if they were regular keywords or standard functions. For example, all of these must parse as valid calls without SQLFluff rewriting the identifier case:
- `SELECT SomeSchema.XValue();`
- `SELECT SomeSchema.Value();`
- `SELECT SomeSchema.VALUE();`

Even though there can be ambiguity with user-defined functions that share names with known datatype methods, SQLFluff should prefer parsing dotted calls of the form `.<name>(...)` as method calls when `<name>` is a known datatype method name, to avoid unsafe case changes that could break code.

After the fix, parsing/linting these constructs in the `tsql` dialect should complete without parser warnings, and the resulting parse tree should correctly represent:
- XML schema collection CREATE/ALTER/DROP statements,
- typed XML type specifications inside `DECLARE`,
- dotted datatype method-call expressions (including chained calls) on arbitrary valid expressions.