import wifi
import ujson
import urequests
import time
from machine import I2C, Pin
from max30102 import MAX30102

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
FLASK_URL = "http://192.168.1.2:5000"

API_TOKEN = "92740f2032f70de06443a3817b5de5eb976b0adb208a559fabee78207aad098e"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + API_TOKEN,
}

SECONDI_SENZA_DITO_PER_STOP = 3

DURATA_MISURAZIONE = 20

# ── BOTTONE KY-004 ─────────────────────────────────────────────────────────────
button = Pin(18, Pin.IN, Pin.PULL_UP)

# ── FUNZIONI API ───────────────────────────────────────────────────────────────
def get_comando():
    try:
        r = urequests.get(FLASK_URL + "/api/comando", headers=HEADERS)
        data = r.json()
        r.close()
        return data.get("comando", "idle")
    except Exception as e:
        print("Errore comando:", e)
        return "idle"


def invia_bpm_live(bpm, stato="misurazione in corso..."):
    try:
        payload = ujson.dumps({
            "bpm": int(bpm),
            "stato": str(stato)
        })

        r = urequests.post(
            FLASK_URL + "/api/bpm_live",
            data=payload,
            headers=HEADERS
        )
        r.close()

    except Exception as e:
        print("Errore BPM live:", e)


# def invia_risultato(bpm_medi, bpm_max, bpm_min):
#     try:
#         # Forza interi puri con // per evitare float nel JSON su MicroPython
#         payload = ujson.dumps({
#             "bpm_medi": bpm_medi // 1,
#             "bpm_max":  bpm_max  // 1,
#             "bpm_min":  bpm_min  // 1,
#         })

#         print("Invio payload:", payload)

#         r = urequests.post(
#             FLASK_URL + "/api/misura",
#             data=payload,
#             headers=HEADERS
#         )

#         data = r.json()
#         r.close()

#         if data.get("ok"):
#             print("Risultato salvato!")
#         else:
#             print("Errore server:", data)

#     except Exception as e:
#         print("Errore invio risultato:", e)


def invia_risultato(bpm_medi, bpm_max, bpm_min):
    try:
        payload = ujson.dumps({
            "bpm_medi": bpm_medi // 1,
            "bpm_max":  bpm_max  // 1,
            "bpm_min":  bpm_min  // 1,
        })

        print("Payload:", payload)

        r = urequests.post(
            FLASK_URL + "/api/misura",
            data=payload,
            headers=HEADERS
        )

        print("Status:", r.status_code)
        print("Risposta:", r.text)

        r.close()

    except Exception as e:
        print("Errore invio risultato:", e)


# ── MISURAZIONE BPM ────────────────────────────────────────────────────────────
def misura_bpm(sensor):

    history = []
    bpm_list = []

    last_beat_time = 0

    tempo_senza_dito = 0
    finger_on = False

    start_time = 0

    print("Metti il dito sul sensore...")
    invia_bpm_live(0, "metti il dito sul sensore...")

    while True:

        sensor.check()

        if sensor.sense.IR.is_empty():
            time.sleep_ms(10)
            continue

        ir = sensor.pop_ir_from_storage()

        # ── DITO ASSENTE ───────────────────────────────────────────────
        if ir < 3000:

            tempo_senza_dito += 10

            if finger_on and tempo_senza_dito >= (SECONDI_SENZA_DITO_PER_STOP * 1000):
                print("Dito rimosso. Fine misurazione.")
                break

            time.sleep_ms(10)
            continue

        # ── DITO PRESENTE ─────────────────────────────────────────────
        tempo_senza_dito = 0

        if not finger_on:
            print("Dito rilevato! Calibrazione...")
            finger_on = True

            invia_bpm_live(0, "calibrazione in corso...")

            start_time = time.ticks_ms()

        # ── STOP DOPO 20 SECONDI ───────────────────────────────
        if finger_on:
            if time.ticks_diff(time.ticks_ms(), start_time) >= (DURATA_MISURAZIONE * 1000):
                print("20 secondi terminati.")
                break

        history.append(ir)

        if len(history) > 30:
            history.pop(0)

        avg = sum(history) / len(history)

        now = time.ticks_ms()

        # rilevazione battito
        if ir > (avg + 60) and time.ticks_diff(now, last_beat_time) > 600:

            if last_beat_time != 0:

                delta = time.ticks_diff(now, last_beat_time)

                current_bpm = 60000 / delta

                if 45 < current_bpm < 160:

                    bpm_list.append(current_bpm)

                    if len(bpm_list) > 15:
                        bpm_list.pop(0)

                    if len(bpm_list) >= 4:

                        avg_bpm = int(sum(bpm_list) / len(bpm_list))

                        invia_bpm_live(avg_bpm, "misurazione in corso...")

                    else:

                        invia_bpm_live(
                            0,
                            "calibrazione " + str(len(bpm_list)) + "/4..."
                        )

            last_beat_time = now

        time.sleep_ms(10)

    # ── RISULTATO FINALE ─────────────────────────────────────────────
    if len(bpm_list) < 4:
        invia_bpm_live(0, "dati insufficienti")
        return None

    # Usa integer division // per garantire int puro su MicroPython
    bpm_medi = int(sum(bpm_list) // len(bpm_list))
    bpm_max  = int(max(bpm_list))
    bpm_min  = int(min(bpm_list))

    print("BPM Medio:", bpm_medi)

    return bpm_medi, bpm_max, bpm_min


# ── WIFI ──────────────────────────────────────────────────────────────────────
rete = wifi.connetti_wifi()

# ── SENSOR ────────────────────────────────────────────────────────────────────
i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)

sensor = MAX30102(i2c=i2c)
sensor.setup_sensor()

sensor.set_pulse_amplitude_red(0xFF)
sensor.set_pulse_amplitude_it(0xFF)
sensor.set_pulse_amplitude_green(0xFF)
sensor.set_pulse_amplitude_proximity(0xFF)

print("Premi il bottone per attivare la misurazione!")

# ── LOOP PRINCIPALE ───────────────────────────────────────────────────────────
while True:

    comando = get_comando()

    if comando == "start" or button.value() == 0:

        print("Avvio misurazione!")

        time.sleep_ms(200)

        risultato = misura_bpm(sensor)

        if risultato:
            bpm_medi, bpm_max, bpm_min = risultato

            invia_risultato(bpm_medi, bpm_max, bpm_min)

        while button.value() == 0:
            time.sleep_ms(10)

    else:
        print(".", end="")

    time.sleep(0.2)