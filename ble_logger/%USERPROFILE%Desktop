import asyncio, json, os, signal
from datetime import datetime
from bleak import BleakScanner, BleakClient

# <<< ZMIANA: Lista (tabela) adresów MAC do monitorowania >>>
# Wpisz tutaj wszystkie adresy MAC swoich urządzeń
TARGET_DEVICES = [
    "DC:1E:D5:1B:30:A6", # Twoje dotychczasowe urządzenie
    "DC:1E:D5:E5:C2:1E", # Przykładowy drugi adres
    "98:3D:AE:42:FE:92", # Przykładowy trzeci adres
]

# <<< BEZ ZMIAN: Charakterystyka i pliki logów >>>
CHR_UUID   = "12345678-1234-5678-1234-56789abcdef1"
LOG_DIR    = os.path.expanduser("~/ble_logger")
LOG_FILE   = os.path.join(LOG_DIR, "presses.jsonl")

# --- Konfiguracja globalna ---
os.makedirs(LOG_DIR, exist_ok=True)
stop_event = asyncio.Event()

def _signal_handler(*_):
    print("\nOtrzymano sygnał zatrzymania, kończenie...")
    stop_event.set()

def append_jsonl(obj):
    """Bezpiecznie dopisuje linię JSON do pliku logu."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[BŁĄD ZAPISU] Nie udało się zapisać do {LOG_FILE}: {e}")

# <<< NOWA FUNKCJA: Zarządza cyklem życia jednego urządzenia >>>
async def manage_device(device_mac: str):
    """
    Niezależna pętla do zarządzania połączeniem z JEDNYM urządzeniem.
    Wyszukuje, łączy, subskrybuje i obsługuje ponowne połączenie.
    """
    
    # Definiujemy handler notyfikacji W ŚRODKU tej funkcji.
    # Dzięki temu ma dostęp do 'device_mac' i wie, który przycisk wysłał dane.
    def on_notify(_handle, data: bytes):
        ts_host = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        try:
            payload = json.loads(data.decode("utf-8"))
        except Exception:
            payload = {"raw": data.decode("utf-8", "replace")}
        
        # <<< ZMIANA: Dodajemy MAC adres do logu! >>>
        record = {"host_ts": ts_host, "mac": device_mac, **payload}
        
        append_jsonl(record)
        print(f"[{device_mac}] Zapis:", record)

    # Główna pętla dla tego urządzenia
    while not stop_event.is_set():
        dev = None
        print(f"[{device_mac}] Wyszukiwanie urządzenia...")
        try:
            # Szukamy tylko tego konkretnego urządzenia
            dev = await BleakScanner.find_device_by_address(device_mac, timeout=5.0)
        except Exception as e:
            print(f"[{device_mac}] Błąd skanowania: {e}")

        if not dev:
            print(f"[{device_mac}] Nie znaleziono. Ponawiam za 5s.")
            await asyncio.sleep(5)
            continue

        print(f"[{device_mac}] Znaleziono. Łączenie...")
        try:
            async with BleakClient(dev) as client:
                if not client.is_connected:
                    continue
                print(f"[{device_mac}] Połączono. Subskrybuję NOTIFY...")

                await client.start_notify(CHR_UUID, on_notify)
                
                # Czekamy, aż połączenie zostanie zerwane lub program się zatrzyma
                while client.is_connected and not stop_event.is_set():
                    await asyncio.sleep(0.2)
                
                print(f"[{device_mac}] Rozłączono. Zatrzymuję notify...")
                try:
                    await client.stop_notify(CHR_UUID)
                except Exception:
                    pass # Ignorujemy błędy przy stop_notify po rozłączeniu
        
        except Exception as e:
            print(f"[{device_mac}] Błąd połączenia lub klienta: {e}")
        
        if stop_event.is_set():
            break
            
        print(f"[{device_mac}] Pętla zakończona, ponawiam za 2s.")
        await asyncio.sleep(2) # Krótka pauza przed próbą ponownego połączenia

# <<< ZMIANA: Główna funkcja 'run' teraz uruchamia zadania dla WSZYSTKICH urządzeń >>>
async def run():
    """Uruchamia zadanie 'manage_device' dla każdego MAC-a z listy TARGET_DEVICES."""
    tasks = []
    for mac in TARGET_DEVICES:
        # Tworzymy zadanie dla każdego urządzenia
        tasks.append(manage_device(mac))
    
    print(f"Uruchamiam monitorowanie dla {len(tasks)} urządzeń...")
    # Uruchamiamy wszystkie zadania równolegle i czekamy na ich zakończenie
    await asyncio.gather(*tasks)
    print("Wszystkie zadania monitorowania zakończone.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        # To jest potrzebne, jeśli Ctrl+C zostanie wciśnięte poza pętlą asyncio
        print("Wykryto KeyboardInterrupt w głównym wątku.")
        stop_event.set()