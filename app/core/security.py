from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# 可以全局复用一个实例
pwd_hasher = PasswordHasher()

def hash_password(plain_password: str) -> str:
    """
    使用 Argon2 对明文密码进行哈希
    """
    return pwd_hasher.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码是否匹配哈希
    """
    try:
        pwd_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False