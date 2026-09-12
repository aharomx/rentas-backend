import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Base de datos
    DB_USER: str = os.getenv("DB_USER", "rentas")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5433")
    DB_NAME: str = os.getenv("DB_NAME", "rentas_db")

    #JWT
    SECRET_KEY:str=os.getenv("SECRET_KEY", "Cambiar en produccion")
    ALGORITHM:str=os.getenv("ALGORITHM","HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS","7"))

settings=Settings()

