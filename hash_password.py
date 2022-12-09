from passlib.context import CryptContext
from getpass import getpass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# from https://stackoverflow.com/questions/9202224/getting-a-hidden-password-input
password = getpass()

hashed_password = get_password_hash(password)
print("Hashed password is:\n" + hashed_password)
