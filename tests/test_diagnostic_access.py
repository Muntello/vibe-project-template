"""Run with Python, psycopg 3 and pglast. Integration tests use an explicit test DSN."""

import csv
import io
import os
import runpy
import unittest
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
dispatcher = runpy.run_path(str(ROOT / "deployment/diagnostics/diag-sql.py"))
guard = runpy.run_path(str(ROOT / ".claude/hooks/guard-prod-access.py"))


class DiagnosticInputTests(unittest.TestCase):
    def test_one_read_query(self):
        for query in ("SELECT 1 LIMIT 1", "SELECT 1 LIMIT 1;", "EXPLAIN SELECT 1"):
            with self.subTest(query=query):
                dispatcher["check_query"](query)
        for query in ("", "SELECT 1; SELECT 2", "EXPLAIN ANALYZE SELECT 1"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                dispatcher["check_query"](query)

    def test_local_host_quoting(self):
        for host in ("localhost", "'localhost'", '"localhost"', "127.0.0.1", "::1"):
            with self.subTest(host=host):
                self.assertIsNone(guard["verdict"](f"psql -h {host} -d test"))
        self.assertIsNotNone(guard["verdict"]("psql -h db.example.test -d test"))


@unittest.skipUnless(os.environ.get("DIAG_TEST_DSN"), "set DIAG_TEST_DSN to a disposable PostgreSQL database")
class PostgreSQLTests(unittest.TestCase):
    def query(self, sql):
        dispatcher["check_query"](sql)
        output = io.StringIO()
        with psycopg.connect(os.environ["DIAG_TEST_DSN"], autocommit=True) as connection:
            dispatcher["run_query"](connection, sql, output)
            self.assertEqual(connection.info.transaction_status, psycopg.pq.TransactionStatus.IDLE)
        return list(csv.reader(io.StringIO(output.getvalue())))

    def test_bounded_select_with_and_without_delimiter(self):
        for suffix in ("", ";", " -- comment"):
            with self.subTest(suffix=suffix):
                self.assertEqual(self.query("SELECT 1 AS n LIMIT 1" + suffix), [["n"], ["1"]])

    def test_transaction_is_read_only(self):
        self.assertEqual(self.query("SELECT current_setting('transaction_read_only')")[1], ["on"])

    def test_server_timeout(self):
        with self.assertRaises(psycopg.errors.QueryCanceled):
            self.query("SELECT pg_sleep(10)")


if __name__ == "__main__":
    unittest.main()
