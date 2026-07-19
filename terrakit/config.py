import json

class Config:
    def __init__(self, filename="config.json"):
        self.filename = filename

        self.data = self.load()

    def load(self):
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            print(f"Fichier de configuration '{self.filename}' non trouvé. Utilisation des valeurs par défaut.")
            return {}
        except json.JSONDecodeError:
            print(f"Erreur lors du décodage du fichier de configuration '{self.filename}'. Utilisation des valeurs par défaut.")
            return {}
        
    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
        self.save()
        