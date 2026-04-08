import socket

HOST = '127.0.0.1'  # adresse du serveur
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))

    # Envoi d'un message (optionnel)
    client.sendall(b"Hello server")

    # Réception de la réponse
    data = client.recv(1024)

    print("Réponse brute :", data)
    print("Réponse décodée :", data.decode('utf-8'))

input("Press any key for exit...")