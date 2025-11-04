#!/usr/bin/env python3
# /usr/local/bin/send_time.py
# Wszechstronny klient RPi:
# 1. Wysyla dane czujnikow (POST /data) - teraz z realnych zdarzen BLE
# 2. Wysyla meldunek czasu (POST /update) - dla utrzymania statusu
# 3. Rejestruje port RPi (POST /register/rasp) - dla powiadomien zwrotnych

import os
import json
import socket
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone
import pytz

# --- KONFIGURACJA ---
# Adres serwera VPS
SERVER_URL = "https://testserwera.pl"  # ZMIEŃ NA TWÓJ ADRES
PASSWORD = "ZMIEN_TO_HASLO_XD"         # Upewnij się, że to hasło jest identyczne jak w server.js

# Port, na którym RPi nasłuchuje (jeśli serwer ma wysyłać coś do RPi)
RPi_LISTEN_PORT = 3001

# ----- KONFIG BLE LOG -----
HOME = str(Path.home())
# Plik z wydarzeniami zapisywany przez Twój logger BLE (ble_btn_logger.py)
BLE_LOG_PATH = os.path.join(HOME, "ble_logger", "presses.jsonl")
# Tu trzymamy bajtowy offset ostatnio wysłanych wydarzeń
BLE_STATE_PATH = os.path.join(HOME, "ble_logger", ".presses.offset")

# Mapowanie przycisku na format API serwera
BTN_GATEWAY_ID = "1"
BTN_SENSOR_ID  = "7"        # zmień jeśli chcesz inny numer sensora
BTN_TYPE       = "button"   # np. "door_contact" jeśli wolisz
BTN_VALUE      = "1"        # „klik” jako "1"


# -------------------- NARZĘDZIA SIECIOWE --------------------
def get_local_ip():
    """Probuje pobrac lokalny adres IP w sieci (np. 192.168.x.x)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Symulacja polaczenia, aby pobrac adres IP interfejsu
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        # Fallback na 127.0.0.1, jesli brak interfejsu
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


# -------------------- POMOCNICZE: ODCZYT ZDARZEŃ BLE --------------------
def _ensure_ble_dir():
    os.makedirs(os.path.dirname(BLE_LOG_PATH), exist_ok=True)


def _read_offset() -> int:
    try:
        with open(BLE_STATE_PATH, "r", encoding="utf-8") as f:
            return int((f.read() or "0").strip())
    except FileNotFoundError:
        return 0
    except Exception:
        return 0


def _write_offset(offset: int):
    try:
        with open(BLE_STATE_PATH, "w", encoding="utf-8") as f:
            f.write(str(offset))
    except Exception:
        # brak offsetu nie jest krytyczny
        pass


def _iso_to_ms(iso_str: str) -> int:
    """
    Zamienia ISO8601 (np. 2025-10-30T21:34:12.345Z) na epoch ms.
    Jeśli brak 'Z' i brak strefy, traktujemy jako UTC.
    """
    try:
        if not iso_str:
            raise ValueError("empty")
        if iso_str.endswith("Z"):
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        # fallback: teraz w PL
        return int(datetime.now(pytz.timezone('Europe/Warsaw')).timestamp() * 1000)


def _read_new_ble_events():
    """
    Czyta TYLKO nowe linie z presses.jsonl, od ostatniego offsetu.
    Zwraca krotkę: (events_list, prev_offset, new_offset)
      - events_list: list[dict]
      - prev_offset: skąd zaczęliśmy czytać (do ewentualnego rollbacku)
      - new_offset: do którego bajtu doczytaliśmy
    """
    _ensure_ble_dir()
    if not os.path.exists(BLE_LOG_PATH):
        return [], _read_offset(), _read_offset()

    events = []
    prev_off = _read_offset()
    new_off = prev_off
    try:
        with open(BLE_LOG_PATH, "rb") as f:
            f.seek(0, os.SEEK_END)
            end = f.tell()
            if prev_off > end:
                # log został zrotowany/skrócony
                prev_off = 0
            f.seek(prev_off, os.SEEK_SET)

            for line in f:
                try:
                    obj = json.loads(line.decode("utf-8"))
                    events.append(obj)
                except Exception:
                    # pomijamy uszkodzone linie
                    pass

            new_off = f.tell()
    except Exception as e:
        print(f"Blad odczytu BLE logu: {e}")
        # w razie błędu nic nie zmieniamy
        return [], prev_off, prev_off

    return events, prev_off, new_off


def get_ble_sensor_data():
    """
    Mapuje zdarzenia 'press' na paczkę do /data.
    Odczytuje nowe linie z presses.jsonl i zwraca listę obiektów zgodnych z API + offsety.
    """
    raw_events, prev_off, new_off = _read_new_ble_events()
    sensor_data_list = []

    for ev in raw_events:
        # Oczekujemy pól z loggera: {"host_ts": "...Z", "mac": "...", "id": 7, ...}
        ts_ms = _iso_to_ms(ev.get("host_ts", ""))

        # <<< POPRAWKA: Pobierz ID bezpośrednio z pliku logu >>>
        # Użyj "id" z pliku .jsonl, a jeśli go nie ma, użyj domyślnego BTN_SENSOR_ID ("7")
        sensor_id_from_log = ev.get("id", BTN_SENSOR_ID)

        # Upewnij się, że ID jest tekstem (stringiem)
        sensor_id_str = str(sensor_id_from_log)

        sensor_data_list.append({
            "gateway_id": BTN_GATEWAY_ID,
            "sensor_id": sensor_id_str,  # <-- Używamy ID odczytanego z pliku!
            "type": BTN_TYPE,
            "value": BTN_VALUE,
            "timestamp": ts_ms
        })

    return sensor_data_list, prev_off, new_off


# -------------------- WYSYŁKA DANYCH --------------------
def send_sensor_data():
    """Czyta nowe zdarzenia BLE i wysyła je do serwera VPS (POST /data)."""
    print("Wykonuje: Wysylanie danych czujnikow do serwera (POST /data)...")
    API_ENDPOINT = f"{SERVER_URL}/data"

    sensor_data, prev_off, new_off = get_ble_sensor_data()
    if not sensor_data:
        print("Brak nowych zdarzen BLE do wyslania.")
        return

    payload = {
        "password": PASSWORD,
        "sensors": sensor_data
    }

    try:
        r = requests.post(API_ENDPOINT, json=payload, timeout=5)
        r.raise_for_status()
        print(f"Dane czujnikow wyslane pomyslnie. Sztuk: {len(sensor_data)}. Serwer status: {r.status_code}")
        # przesuwamy offset dopiero po sukcesie
        _write_offset(new_off)
    except Exception as e:
        print(f"Blad wysylania danych czujnikow: {e}")
        # nie zmieniamy offsetu — spróbujemy ponownie przy następnym wywołaniu
        _write_offset(prev_off)


def send_time_report():
    """Wysyła meldunek czasu i szczegóły IP do serwera VPS (POST /update)."""
    print("Wykonuje: Wysylanie meldunku czasu (POST /update)...")
    API_ENDPOINT = f"{SERVER_URL}/update"

    local_ip = get_local_ip()
    local_time = datetime.now(pytz.timezone('Europe/Warsaw')).strftime('%Y-%m-%d %H:%M:%S %Z')

    report_text = (
        f"Ostatni meldunek (RPi):\n"
        f"Czas lokalny: {local_time}\n"
        f"Lokalny IP: {local_ip}\n"
        f"Serwer nasluchuje na porcie: {RPi_LISTEN_PORT}\n"
    )

    payload = {
        "password": PASSWORD,
        "text": report_text
    }

    try:
        r = requests.post(API_ENDPOINT, json=payload, timeout=5)
        r.raise_for_status()
        print(f"Meldunek czasu wyslany pomyslnie. Serwer status: {r.status_code}")
    except Exception as e:
        print(f"Blad wysylania meldunku czasu: {e}")


def register_rpi_ip():
    """Wysyla port RPi, aby serwer VPS pobral publiczny adres IP."""
    print("Wykonuje: Rejestracja portu RPi (POST /register/rasp)...")
    API_ENDPOINT = f"{SERVER_URL}/register/rasp"
    payload = {
        "password": PASSWORD,
        "port": RPi_LISTEN_PORT
    }
    try:
        r = requests.post(API_ENDPOINT, json=payload, timeout=5)
        r.raise_for_status()
        print(f"Port RPi zarejestrowany. Publiczny IP pobrano przez Serwer.")
    except Exception as e:
        print(f"Blad rejestracji portu RPi: {e}")


# -------------------- URUCHOMIENIE LOGIKI GLOWNEJ --------------------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'register':
        # Specjalny tryb tylko do jednorazowej rejestracji IP
        register_rpi_ip()
    else:
        # Domyślnie (np. co minutę przez cron):
        # 1. Wyslij dane czujnikow z BLE (jeśli są)
        send_sensor_data()
        # 2. Wyslij meldunek czasu (do sprawdzenia statusu RPi)
        send_time_report()
        # 3. Upewnij sie, ze IP jest zarejestrowane (mozna robic rzadziej)
        register_rpi_ip()
