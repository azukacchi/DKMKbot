import sqlite3
import os.path
from main import createtable
import config


filename = 'yourdatabasefile.db'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, filename)

createtable(db_path)



