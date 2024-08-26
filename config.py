import os
import logging

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log_level
)

vtv_plantas = {
    "00001": "Donado",
    "00002": "27 de Febrero",
    "00003": "Velez Sarsfield",
    "00004": "Santa Maria del Buen Ayre",
    "00005": "Osvaldo Cruz",
    "00006": "Tronador",
    "00007": "9 de Julio Sur"
}

meses = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}


TELEGRAM_BOT_API_KEY = os.getenv("TELEGRAM_BOT_API_KEY")
database_path = os.getenv("DATABASE_PATH", "./vtv_turnos.db")
