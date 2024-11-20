from src.config import PUBLIC_KEY, PRIVATE_KEY
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64



def encrypt_data(plain_text: str) -> str:
    encrypted = PUBLIC_KEY.encrypt(
        plain_text.encode(),
        # Optimal Asymmetric Encryption Padding
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_data(encrypted_data: str) -> str:
    decrypt_data = PRIVATE_KEY.decrypt(
        base64.b64decode(encrypted_data.encode('utf8')),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypt_data.decode('utf-8')

if __name__ == "__main__":
    # # Example to encrypt
    # plain_text = "password123"
    # encrypted_password = encrypt_data(plain_text)
    # print("encrypted password", encrypted_password)

    # Example to decypt
    res = decrypt_data("XX8JskEVnCO3vb8WlRhpE8c+houpMdFspQLSfjOFMgQX8Foe+WGpGG7GVPLl3+mjOMGf0oHqd2nGjRmt5zbhXou5WvcS1QvPA1igX2+RHeSLlmmRKo0ye7wbMmjj9Ly04oinJR5McW7Zk1nXI6dwN5hPu58nedGXWpjU2PSTrH3HAjppv+g+Rkhq8NfTpppFnwXkIxhUDkVrVpELihF3zkL1mC3+XH1K09uUJRlF56bg3GBQbDuY8ngBoL523jeX4heG1ctLcWoEWyAib9YPPw3XdHfhM4slxszyAGEIpVKnDpbnUpfuWYItUSUYSEeS9f24P9R9rFg+TMFFtlSWDw==")
    print(res)