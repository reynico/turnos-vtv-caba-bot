import unittest
from unittest.mock import patch, MagicMock
import sqlite3
from database import query_vtv, store_turnos_in_db, create_db
import json


class TestVTVBot(unittest.TestCase):
    @patch('requests.post')
    def test_query_vtv(self, mock_post):
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            'result': [
                {'fecha': '10/10/2024', 'idPlanta': '00001', 'tramiteDisponible': 'True'}
            ]
        }).encode('utf-8')
        mock_post.return_value = mock_response

        result = query_vtv(mes=10, year=2024)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['fecha'], '10/10/2024')
        self.assertEqual(result[0]['idPlanta'], '00001')

    def test_store_turnos_in_db(self):
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE turnos (
                id INTEGER PRIMARY KEY,
                plant TEXT,
                date TEXT,
                month INTEGER,
                year INTEGER,
                UNIQUE(plant, date, month, year)
            )
        ''')
        conn.commit()

        turnos = [
            {'fecha': '10/10/2024', 'idPlanta': '00001', 'tramiteDisponible': 'True'},
            {'fecha': '11/10/2024', 'idPlanta': '00002', 'tramiteDisponible': 'True'}
        ]

        store_turnos_in_db(conn, 10, 2024, turnos)

        cursor.execute("SELECT * FROM turnos")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], '00001')
        self.assertEqual(rows[0][2], '2024-10-10')
        self.assertEqual(rows[0][3], 10)
        self.assertEqual(rows[0][4], 2024)

    def test_create_db(self):
        conn = create_db()

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='turnos'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'turnos')

        conn.close()


if __name__ == '__main__':
    unittest.main()
