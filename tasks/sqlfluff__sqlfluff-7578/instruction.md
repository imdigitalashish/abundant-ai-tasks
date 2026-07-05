SQLFluff’s T-SQL dialect parser fails to parse several valid T-SQL constructs related to XML schema collections, typed XML declarations, and datatype “method” calls. Attempting to lint/parse these statements produces a parse warning (e.g., SQLFluff(PRS)) even though the SQL is valid.

The parser must be updated so that the following T-SQL syntax is accepted and parsed successfully:

1) XML SCHEMA COLLECTION DDL statements
- CREATE XML SCHEMA COLLECTION with a schema name (optionally schema-qualified) and an AS clause whose body can be either a string literal (often an N-prefixed Unicode string) or a variable.
  Examples:
  - CREATE XML SCHEMA COLLECTION dbo.SomeXmlSchemaCollection AS N'<schema ...>';
  - DECLARE @MySchemaCollection AS NVARCHAR(MAX) = '';
    CREATE XML SCHEMA COLLECTION AnotherXmlSchemaCollection AS @MySchemaCollection;
- ALTER XML SCHEMA COLLECTION <name> ADD <xml_schema_source> where <xml_schema_source> can be a string literal or a variable.
  Examples:
  - ALTER XML SCHEMA COLLECTION MyColl ADD '<schema ...>';
  - ALTER XML SCHEMA COLLECTION dbo.MyColl ADD @NewItem;
- DROP XML SCHEMA COLLECTION <name>;

These statements should work both with and without schema qualification (e.g., dbo.SomeXmlSchemaCollection vs AnotherXmlSchemaCollection), and they may appear in scripts that include batch separators like GO.

2) Typed XML declarations
The parser must accept typed XML type specifications used in declarations, including optional DOCUMENT and schema-qualified schema collection names.
Examples:
- DECLARE @typed_xml XML (SomeSchemaCollection);
- DECLARE @typed_xml XML (dbo.SomeSchemaCollection);
- DECLARE @typed_xml XML ([dbo].[SomeSchemaCollection]);
- DECLARE @typed_xml_document XML (DOCUMENT dbo.SomeSchemaCollection);

3) Datatype method-call expressions (XML, hierarchyid, geometry/geography, etc.)
T-SQL supports calling methods on expressions using dot notation, e.g. <expression>.<MethodName>(...). The parser currently mis-parses or rejects these, and in some cases treats the method name like a normal function/identifier in a way that causes unsafe case normalization.

The parser must correctly parse method calls in these forms:
- Called on a column/variable:
  - SELECT @XML.value('.', 'nvarchar(max)');
  - SELECT SomeColumn.value();
- Called on the result of a function:
  - SELECT CONVERT(xml, N'<r></r>').value('.','nvarchar(max)');
  - SELECT convert(hierarchyid, '/1/1/2').GetAncestor(2) parent;
- Called on a subquery expression:
  - SELECT (SELECT CONVERT(xml, N'<r></r>')).value('.','nvarchar(max)');
- Chained method calls:
  - SELECT convert(hierarchyid, '/1/1/2').GetAncestor(2).GetAncestor(2) parent;
  - select @xml.query('.').query('.');
- Other examples that should parse:
  - SELECT @hierarchyid.GetAncestor(2) parent_id;
  - select @geometry.STEndPoint() EndPt;
  - SELECT @geography.STArea() area;
  - SELECT @geography.STDistance(@other_geography) dist;

Method names must be treated as method identifiers in this dot-call position so that SQLFluff does not rewrite their case during fixes. In particular, dotted method calls must support known method names (e.g., value, query, GetAncestor, STEndPoint, STArea, STDistance) and should not fail parsing due to case differences.

Expected behavior: All examples above should parse cleanly under the tsql dialect with no PRS parse warnings, and method names in <expr>.<method>(...) should be preserved (not case-normalized) as written.

Actual behavior: Parsing these statements currently triggers SQLFluff(PRS) warnings and/or mis-parses dotted datatype methods, sometimes treating the method name like a regular function identifier and allowing case-changing behavior that can break T-SQL method calls.