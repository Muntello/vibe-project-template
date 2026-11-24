#!/opt/diag-sql/bin/python -I
"""Run one diagnostic query on a configured local PostgreSQL database."""

import csv
import os
import re
import sys
from contextlib import closing
from pathlib import Path

import psycopg
from pglast import ast, parse_sql
from pglast.parser import ParseError


DATABASES = Path("/etc/diag-sql/databases")
MAX_QUERY_BYTES = 65536


def check_query(query):
    statements = parse_sql(query)
    if len(statements) != 1:
        raise ValueError("send one SELECT or plain EXPLAIN per call")
    statement = statements[0].stmt
    if isinstance(statement, ast.ExplainStmt):
        if any(option.defname == "analyze" for option in statement.options or ()):
            raise ValueError("use EXPLAIN without ANALYZE")
        statement = statement.query
    if not isinstance(statement, ast.SelectStmt) or statement.intoClause or statement.lockingClause:
        raise ValueError("expected a read-only SELECT")
    # Query-shape hints for operators. Database permissions and the read-only
    # transaction also apply to nested queries and functions.
    for pattern, reason in (
        (r"\blike\s*'%|\bilike\s*'%", "a leading-wildcard LIKE"),
        (r"~|\bsimilar\s+to\b", "a regex match"),
        (r"::\s*(?:text|varchar)\b", "a cast to text"),
    ):
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError("refused " + reason)


def run_query(connection, query, output):
    with connection.transaction(force_rollback=True):
        connection.execute("SET TRANSACTION READ ONLY")
        connection.execute("SET LOCAL statement_timeout = '8s'")
        connection.execute("SET LOCAL lock_timeout = '2s'")
        writer = csv.writer(output)
        with connection.cursor() as cursor, closing(cursor.stream(query)) as rows:
            first = next(rows, None)
            if cursor.description:
                writer.writerow([column.name for column in cursor.description])
            if first is not None:
                writer.writerow(first)
                writer.writerows(rows)


def main():
    databases = DATABASES.read_text().split()
    if len(sys.argv) > 2 or not databases:
        raise ValueError("usage: diag-sql [configured-database] < query.sql")
    database = sys.argv[1] if len(sys.argv) == 2 else databases[0]
    if database not in databases:
        raise ValueError("database is not configured for diagnostics")
    data = sys.stdin.buffer.read(MAX_QUERY_BYTES + 1)
    if len(data) > MAX_QUERY_BYTES:
        raise ValueError("diagnostic SQL exceeds 64 KiB")
    query = data.decode("utf-8")
    check_query(query)
    # The caller supplies SQL and a database name only. Read no caller-supplied
    # libpq connection settings when running under the peer-authenticated user.
    for name in tuple(os.environ):
        if name.startswith("PG"):
            del os.environ[name]
    with psycopg.connect(host="/var/run/postgresql", user="diagnostic_user",
                         dbname=database, connect_timeout=3, autocommit=True) as connection:
        run_query(connection, query, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, ParseError, psycopg.Error) as error:
        sys.exit(f"diag-sql: {error}")
