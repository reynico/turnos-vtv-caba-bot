import time
from datetime import datetime
from database import create_db, store_turnos_in_db, query_vtv
import logging


def update_turnos_periodically(conn):
    current_year = datetime.now().year
    years_to_check = [current_year, current_year + 1]
    while True:
        for year in years_to_check:
            for month in range(1, 13):
                turnos = query_vtv(month, year)
                if turnos and len(turnos) > 0:
                    logging.info(f"Found {len(turnos)} turnos on {month}/{year}")
                    store_turnos_in_db(conn, month, year, turnos)
                else:
                    logging.warning(f"No new turnos found on {month}/{year}")
        logging.info("Periodic action ran successfully, waiting 60 minutes for next round")
        time.sleep(3600)


if __name__ == '__main__':
    conn = create_db()
    update_turnos_periodically(conn)
