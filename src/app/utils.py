import os
import json

from src.config import BASE_DIR

class IpsManagement:
    """Basic class to save and get the IPs"""
    def __init__(self) -> None:
        self.file = os.path.join(BASE_DIR, "security/ips_management.json")
        self.data = self.load_file()

    def load_file(self):
        if not os.path.exists(self.file):
            return {}
        with open(self.file, 'r') as f:
            return json.load(f)

    def save_file(self):
        with open(self.file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_ip(self, ip):
        return self.data.get(ip, None)

    def set_new_ip(self, ip, attributes = None):
        self.data[ip] = attributes
        self.save_file()

    def get_ips(self) -> list:
        return list(self.data.keys())


if __name__ == "__main__":
    ips = IpsManagement()

    a = ips.get_ips()
    print(a)