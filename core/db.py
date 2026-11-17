import os, psycopg2
from dotenv import load_dotenv
load_dotenv()

def conn():
    return psycopg2.connect(os.environ["DB_DSN"])
