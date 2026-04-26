import socket
import json

HOST = '0.0.0.0'
PORT = 5000

# Données JSON à envoyer
response_data = {
    "status": "ok",
    "message": "Hello from server",
    "code": 200
}

# Conversion en JSON (string)
response_json = json.dumps(response_data)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen()

    print(f"Serveur en écoute sur {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        with conn:
            print(f"Connexion de {addr}")

            data = conn.recv(1024)  # lit les données envoyées (optionnel)
            print(f"Reçu: {data}")

            # Envoi du JSON (encodé en bytes)
            conn.sendall(response_json.encode('utf-8'))