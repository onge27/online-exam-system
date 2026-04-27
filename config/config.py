import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'examSystemSecretKey2024!')
    DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
    DEBUG = True
