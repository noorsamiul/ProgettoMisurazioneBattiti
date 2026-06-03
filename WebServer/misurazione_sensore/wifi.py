import network
import time

def connetti_wifi():
    ssid = "VODAFONE-E10336597"
    password = "dh6EFAeNPaeLJpeM"
    # ssid = "BancoSperimentale2G"
    # password = "Galileo19"

    wlan = network.WLAN(network.STA_IF)

    # Reset WiFi
    wlan.active(False)
    time.sleep(1)

    wlan.active(True)
    time.sleep(1)

    if not wlan.isconnected():
        print("Connessione al WiFi...")
        wlan.connect(ssid, password)

        timeout = 15

        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        print("\nConnesso! IP:", wlan.ifconfig()[0])
        return wlan
    else:
        raise OSError("Connessione WiFi fallita")