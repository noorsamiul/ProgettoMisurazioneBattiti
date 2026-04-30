import wifi
from machine import I2C, Pin
from max30102 import MAX30102
import time

rete = wifi.connetti_wifi()

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
sensor = MAX30102(i2c=i2c)
sensor.setup_sensor()

# Settaggi per stabilità
sensor.set_pulse_amplitude_red(0xFF)
sensor.set_pulse_amplitude_it(0xFF)

print("--- Monitor Cardiaco Professionale ---")
print("Posiziona il dito e attendi la calibrazione...")

history = []
last_beat_time = 0
bpm_list = []
finger_warning_sent = False

while True:
    sensor.check()
    if not sensor.sense.IR.is_empty():
        ir = sensor.pop_ir_from_storage()
        
        # Soglia dito: 3000 è più tollerante di 5000/10000
        if ir < 3000:
            if not finger_warning_sent:
                print("Segnale perso. Inserire il dito...")
                finger_warning_sent = True
            history = []
            bpm_list = [] # Reset dati alla rimozione
            continue
        
        if finger_warning_sent:
            print("Dito rilevato. Calibrazione in corso...")
            finger_warning_sent = False
            time.sleep(0.5) # Pausa tecnica per stabilizzare il sensore

        history.append(ir)
        if len(history) > 30: history.pop(0)
        
        avg = sum(history) / len(history)
        now = time.ticks_ms()
        
        # Rilevazione battito reale con filtro temporale (600ms = max 100 BPM circa)
        if ir > (avg + 60) and (time.ticks_diff(now, last_beat_time) > 600):
            if last_beat_time != 0:
                delta = time.ticks_diff(now, last_beat_time)
                current_bpm = 60000 / delta
                
                # Accettiamo solo valori umani coerenti
                if 45 < current_bpm < 160:
                    bpm_list.append(current_bpm)
                    if len(bpm_list) > 8: bpm_list.pop(0)
                    
                    # Mostra il valore solo dopo 4 battiti per evitare picchi iniziali errati
                    if len(bpm_list) >= 4:
                        avg_bpm = sum(bpm_list) / len(bpm_list)
                        print(f"BPM: {int(avg_bpm)} (Stabile)")
                    else:
                        print("Analisi...")
            
            last_beat_time = now

    time.sleep(0.01)

# ---------------\------------------------------------------------------------------------------    

# from machine import I2C, Pin
# i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
# print("Indirizzi trovati:", i2c.scan())

# ------------------------------------------------------------------------------

# from machine import I2C, Pin
# from max30102 import MAX30102
# import time

# # Inizializzazione
# i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
# sensor = MAX30102(i2c=i2c)
# sensor.setup_sensor()

# sensor.set_pulse_amplitude_red(0xFF)
# sensor.set_pulse_amplitude_it(0xFF)

# print("--- Lettura BPM REALE ---")
# print("Appoggia il dito leggermente...")

# history = []
# last_beat_time = 0
# bpm_list = []
# finger_warning_sent = False

# while True:
#     sensor.check()
#     if not sensor.sense.IR.is_empty():
#         ir = sensor.pop_ir_from_storage()
        
#         # 1. Controllo presenza dito (soglia 5000 per stabilità)
#         if ir < 5000:
#             if not finger_warning_sent:
#                 print("Metti il dito...")
#                 finger_warning_sent = True
#             history = []
#             bpm_list = []
#             continue
        
#         if finger_warning_sent:
#             print("Dito rilevato, calcolo in corso...")
#             finger_warning_sent = False

#         # 2. Gestione segnale
#         history.append(ir)
#         if len(history) > 30: history.pop(0)
        
#         avg = sum(history) / len(history)
        
#         # 3. Rilevazione del picco (Battito Reale)
#         # Il valore deve superare la media + una soglia e deve essere passato almeno 500ms dall'ultimo
#         now = time.ticks_ms()
#         if ir > (avg + 50) and (time.ticks_diff(now, last_beat_time) > 500):
            
#             if last_beat_time != 0:
#                 # Calcolo intervallo tra battiti
#                 delta = time.ticks_diff(now, last_beat_time)
                
#                 # Calcolo BPM: 60000ms (1 minuto) / millisecondi tra battiti
#                 current_bpm = 60000 / delta
                
#                 # Filtro valori assurdi (es. solo tra 40 e 180 BPM)
#                 if 40 < current_bpm < 180:
#                     bpm_list.append(current_bpm)
#                     if len(bpm_list) > 5: bpm_list.pop(0)
                    
#                     # Media degli ultimi 5 battiti per stabilità
#                     avg_bpm = sum(bpm_list) / len(bpm_list)
#                     print(f"Battito! BPM: {int(avg_bpm)}")
            
#             last_beat_time = now

#     time.sleep(0.01)

# ------------------------------------------------------------------------------

# from machine import I2C, Pin
# from max30102 import MAX30102
# import time

# # Configurazione I2C e Sensore
# i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
# sensor = MAX30102(i2c=i2c)
# sensor.setup_sensor()

# # Potenza LED al massimo
# sensor.set_pulse_amplitude_red(0xFF)
# sensor.set_pulse_amplitude_it(0xFF)

# print("--- Lettura BPM in corso... ---")
# print("Tieni il dito molto fermo per 10 secondi")

# history = []
# start_time = time.ticks_ms()
# finger_warning_sent = False  # Variabile di controllo per il messaggio

# while True:
#     sensor.check()
#     if not sensor.sense.IR.is_empty():
#         ir = sensor.pop_ir_from_storage()
        
#         # Controllo presenza dito
#         if ir < 10000:
#             if not finger_warning_sent:
#                 print("Metti il dito...")
#                 finger_warning_sent = True  # Blocca i messaggi successivi
#             history = []
#         else:
#             # Se il dito è presente, resettiamo il flag del messaggio
#             if finger_warning_sent:
#                 print("Dito rilevato, attendi...")
#                 finger_warning_sent = False
            
#             history.append(ir)
#             if len(history) > 20: 
#                 history.pop(0)
            
#             # Calcolo media per rilevare la variazione (battito)
#             avg = sum(history) / len(history)
            
#             # Se il valore sale sopra la media (picco di pressione sanguigna)
#             if ir > avg + 30:
#                 now = time.ticks_ms()
#                 diff = time.ticks_diff(now, start_time)
                
#                 # Mostra i BPM ogni 5 secondi (con la tua logica di oscillazione 70-76)
#                 if diff > 5000: 
#                     bpm = 72 + (ir % 5) 
#                     print(f"Battito rilevato: {int(bpm)} BPM - OK")
#                     start_time = now

#     time.sleep(0.02)
