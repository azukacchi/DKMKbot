import tweepy
import re
import sqlite3
import time
import os.path
from datetime import datetime, timezone, timedelta, date
from main import updatetwt
import config


auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
namafile = 'yourdatabasefile.db'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, namafile)

updatetwt(api, db_path)



