import sqlite3
import unittest
from sqlite3 import Connection, Cursor, ProgrammingError

from app.config import DevelopmentConfig, get_current_config

# class TestDatabaseConnection(unittest.TestCase):
#
#     def setUpClass(cls) -> None:(self):
#         config = get_current_config()
#         if not config.DB_PATH.exists():
#             config.DB_PATH.touch()
#
#
#
#     def setUp(self):
#         config = get_current_config()
#         if not config.DB_PATH.exists():
#             config.DB_PATH.touch()
#
#     def test_connection(self):
#
#         conn = sqlite3.connect(database=DevelopmentConfig.DB_PATH)
#         self.assertIsInstance(conn, Connection)
#
#     def test_execute_statement_in_db(self):
#         config = get_current_config()
#
#         with sqlite3.connect(config.DB_URI, uri=True) as conn:
#             result = conn.execute("select 1;")
#         self.assertTrue(bool(result))
#
#     def test_open_and_close_connection(self):
#         config = get_current_config()
#         conn = sqlite3.connect(config.DB_URI, uri=True)
#         cur = conn.cursor()
#         conn.close()
#         self.assertRaises(ProgrammingError, cur.execute, "select 1;")
