import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from telegram_bot import initialize_db, log_request, get_available_dates, store_notification_request, send_notification
from telegram import Update


class TestVTVBot(unittest.TestCase):

    @patch('sqlite3.connect')
    def test_initialize_db(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        initialize_db()

        self.assertTrue(mock_cursor.execute.called)
        self.assertEqual(mock_cursor.execute.call_count, 3)
        mock_conn.commit.assert_called_once()

    @patch('sqlite3.connect')
    def test_log_request(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=12345, username='testuser')
        update.effective_chat = MagicMock(id=67890)
        update.message = MagicMock(text="Test message")

        log_request(update, command="/start", plant="Donado")

        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0][1]
        self.assertEqual(args[0], 12345)
        self.assertEqual(args[1], "testuser")
        self.assertEqual(args[2], 67890)
        self.assertEqual(args[3], "Test message")
        self.assertEqual(args[4], "/start")
        self.assertEqual(args[5], "Donado")

    @patch('sqlite3.connect')
    def test_get_available_dates(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [("2024-09-01",), ("2024-09-02",)]

        dates = get_available_dates("00001", 9, 2024)

        self.assertEqual(dates, ["2024-09-01", "2024-09-02"])
        mock_cursor.execute.assert_called_once_with("SELECT date FROM turnos WHERE plant = ? AND month = ? AND year = ?",
                                                    ("00001", 9, 2024))

    @patch('sqlite3.connect')
    def test_store_notification_request(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        store_notification_request(12345, "00001", 9, 2024)

        mock_cursor.execute.assert_called_once_with(
            "INSERT OR IGNORE INTO user_notifications (user_id, plant, month, year) VALUES (?, ?, ?, ?)",
            (12345, "00001", 9, 2024)
        )
        mock_conn.commit.assert_called_once()

    @patch('telegram_bot.sqlite3.connect')
    @patch('telegram_bot.Application.builder')
    @patch('telegram_bot.get_available_dates')
    @patch('telegram_bot.Application.bot.send_message', new_callable=AsyncMock)
    async def test_send_notification(self,
                                     mock_send_message,
                                     mock_get_available_dates,
                                     mock_application_builder,
                                     mock_connect
                                     ):
        mock_get_available_dates.return_value = ["2024-09-11", "2024-09-12"]

        mock_app = MagicMock()
        mock_application_builder.return_value.build.return_value = mock_app

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        await send_notification(12345, "00001", 9, 2024)

        mock_send_message.assert_called_once_with(
            chat_id=12345,
            text="Hay nuevos turnos disponibles en la planta de Donado para Septiembre!\n\n2024-09-11\n2024-09-12"
        )



if __name__ == '__main__':
    unittest.main()
