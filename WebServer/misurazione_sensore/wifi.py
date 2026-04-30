import network
import time

def connetti_wifi():
    ssid = "BancoSperimentale2G"
    password = "Galileo19"
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connessione al WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
            print(".", end="")
            
    print('\nConnesso! IP:', wlan.ifconfig()[0])
    return wlan

