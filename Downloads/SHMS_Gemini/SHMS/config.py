import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR   = os.path.join(BASE_DIR, 'database')

# Auto-create database folder so it never fails on any OS
os.makedirs(DB_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shms-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DB_DIR, 'shms.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
