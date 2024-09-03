import requests
import json
import sqlite3
from datetime import datetime
from config import vtv_plantas, database_path
import logging


def query_vtv(mes, year):
    url = 'https://www.suvtv.com.ar/controller/ControllerDispatcher.php'
    plantas_data = "&".join([f"plantas%5B%5D={plant}" for plant in vtv_plantas])
    raw_data = f'controllerName=AgendaController&actionName=obtenerDiasDisponibles&{plantas_data} \
        &sobreTurno=false&mes={mes}&year={year}'

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-language': 'en-US,en;q=0.6',
        'Connection': 'keep-alive',
        'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.suvtv.com.ar',
        'Referer': 'https://www.suvtv.com.ar/turnos',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/109.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    response = requests.post(url, headers=headers, data=raw_data)

    try:
        json_data = json.loads(response.content)
        return json_data['result']
    except json.decoder.JSONDecodeError:
        logging.error(f"Couldn't load turnos JSON data. Raw response: {response.content}")
    return False


def store_turnos_in_db(conn, month, year, turnos):
    cursor = conn.cursor()

    if turnos:
        logging.info(f"Deleting existing {len(turnos)} turnos")
        cursor.execute('''
            DELETE FROM turnos
            WHERE month = ? AND year = ?
        ''', (month, year))

    for turno in turnos:
        date_str = turno['fecha']  # Assume this is in 'DD/MM/YYYY' format
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        plant = turno['idPlanta']

        logging.info(f"Storing turno {date_str} for planta {vtv_plantas[plant]}")
        turno_month = month if month is not None else date_obj.month
        turno_year = year if year is not None else date_obj.year

        cursor.execute('''
            INSERT OR IGNORE INTO turnos (plant, date, month, year)
            VALUES (?, ?, ?, ?)
        ''', (plant, date_obj.strftime('%Y-%m-%d'), turno_month, turno_year))

    conn.commit()


def create_db():
    logging.info(f"database_path: {database_path}")
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY,
            plant TEXT,
            date TEXT,
            month INTEGER,
            year INTEGER,
            UNIQUE(plant, date, month, year)
        )
    ''')
    conn.commit()
    return conn
