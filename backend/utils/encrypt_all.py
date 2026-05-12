# encrypt_all.py
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

def encrypt_password(password: str):
    ph = PasswordHasher()
    hashed_password = ph.hash(password)
    return hashed_password

def verify_password(hashed_password: str, password: str):
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, password)
        return True
    except VerificationError:
        return False



