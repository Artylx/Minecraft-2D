import subprocess
import sys

requirements = [
    "pygame",
    "tomlkit",
    "matplotlib",
    "noise",
    "uuid",
]

def install():
    for package in requirements:
        try:
            print(f"Installation de {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(f"Erreur avec {package}: {e}")

if __name__ == "__main__":
    install()
    print("Installation terminée.")