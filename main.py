import tweepy
import re
import sqlite3
import time
import os.path
from datetime import datetime, timezone, timedelta, date


def createtable(db_path):
    # making a database file and the table 

    connection = sqlite3.connect(db_path)
    create_twt_table = '''CREATE TABLE IF NOT EXISTS tweets (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT NOT NULL,
        Time DATETIME NOT NULL,
        Tweet TEXT NOT NULL,
        RTStatus INTEGER,
        DMSender INTEGER);'''

    cursor = connection.cursor()
    cursor.execute(create_twt_table)
    connection.commit()

    cursor.close()
    connection.close()

    return


def updatetwt(api, db_path):
    '''Collecting tweets through api.search api.favorites
    '''
    # checking newest tweets to 7 days back
    n = 40
    search_words = 'YOUR-OTP-NAME-HERE' #put your keywords here
    criteria='min_faves:15 filter:media' #example of filter and criteria
    date_since = date.today() - timedelta(days=7)
    
    new_search = search_words + " " + criteria
    tweets = tweepy.Cursor(api.search, q=new_search, lang='ko', since=date_since, tweet_mode='extended').items(n)
    items = []
    twtid = []
    twtdate = []
    username = []

    for tweet in tweets:
        item = []
        item.append(' '.join(re.sub("(@[A-Za-z0-9]+)|(\w+:\/\/\S+)", " ",tweet.full_text.lower()).split()))
        #item.append(tweet.full_text)
        items.append(item[0])
        username.append(tweet.user.screen_name)
        twtid.append(tweet.id)
        twtdate.append(tweet.created_at)

    #checking the favorite tabs (which I do manually to collect contents other than 7 days)
    tweets2 = tweepy.Cursor(api.favorites, q=api.me().screen_name, tweet_mode='extended', lang='ko').items()

    for tweet in tweets2:
        item = []
        item.append(' '.join(re.sub("(@[A-Za-z0-9]+)|(\w+:\/\/\S+)", " ",tweet.full_text.lower()).split()))
        items.append(item[0])
        username.append(tweet.user.screen_name)
        twtid.append(tweet.id)
        twtdate.append(tweet.created_at)
        api.destroy_favorite(tweet.id)
    

    connection = sqlite3.connect(db_path)
    crud_query = '''INSERT OR IGNORE INTO tweets (ID, Username, Time, Tweet) values (?,?,?,?);'''

    zipobj = zip(twtid, username, twtdate, items)
    input_list = [*zipobj]

    cursor = connection.cursor()
    cursor.executemany(crud_query,input_list)
    connection.commit()

    cursor.close()
    connection.close()

    print('Tweet database has been updated.')
    time.sleep(3)

    return

def retweet(api, db_path):
    '''Calling for tweet that hasn't been retweeted yet from the database
    '''
      
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('SELECT ID, RTStatus, DMSender FROM tweets WHERE \
    RTStatus == 2 OR RTStatus IS NULL ORDER BY RTStatus DESC, Time')
    datafin1 = cursor.fetchmany(1)
    connection.commit()
        
    idtwt = [twt[0] for twt in datafin1]
    rtstatus = [twt[1] for twt in datafin1]
    dmsender = [twt[2] for twt in datafin1]


    for id in idtwt:
        api.retweet(id=id)

    if rtstatus == 2:
        senddm(api, dmsender)

    for id in idtwt:
        cursor.execute('UPDATE tweets SET RTStatus=1 WHERE ID=?', (id,))
    connection.commit()

    cursor.close()
    connection.close()

    print('Retweet is finished.')
    time.sleep(3)

    return 


def checkdm(api, db_path):
    '''Checking any suggestion sent through DM.
    The DM should contain triggerword + link to the suggested tweet.
    '''
    dms = api.list_direct_messages(count=15)

    #isidm = []
    items = []
    username = []
    twtdate = []
    twtid = []
    dmsender = []
    for dm in dms:
        
        if '(YOUR-TRIGGER-WORD-HERE)' in dm.message_create['message_data']['text']:
            urls = dm.message_create['message_data']['entities']['urls']
            if len(urls) >0:
                linkcontent = urls[0]['expanded_url']
                regex = r'(?=twitter\.com\/\w+\/status\/(\d+))'
                dmtwtid = int(re.findall(regex, linkcontent)[0])
                #isidm.append(dmtwtid)
            
                try:        
                    tweet = api.get_status(id=dmtwtid, tweet_mode='extended')
                    if tweet.user.id == api.me().screen_name:
                        continue
                    else:
                        item = []
                        item.append(' '.join(re.sub("(@[A-Za-z0-9]+)|(\w+:\/\/\S+)", " ",tweet.full_text.lower()).split()))
                        item.append(tweet.full_text)
                        items.append(item[0])
                        username.append(tweet.user.screen_name)
                        twtid.append(tweet.id)
                        twtdate.append(tweet.created_at)
                        dmsender.append(dm.message_create['sender_id'])
                except: continue
            else: continue

    #df = pd.DataFrame(data=list(zip(twtid, username, twtdate, items, dmsender)))
    #display(df)
        
    connection = sqlite3.connect(db_path)
    crud_query = '''INSERT OR IGNORE INTO tweets (ID, Username, Time, Tweet, RTStatus, DMSender) values (?,?,?,?,2,?);'''

    zipobj = zip(twtid, username, twtdate, items, dmsender)
    input_list = [*zipobj]

    cursor = connection.cursor()
    cursor.executemany(crud_query,input_list)
    connection.commit()

    cursor.close()
    connection.close()
    
    print('DM has been checked')
    time.sleep(3)

    return


def senddm(api, dmsender):
    
    # adjust your timezone here when you want to send a DM notifying that the
    # suggested tweet has been retweeted
    rttime = datetime.now().astimezone(timezone(timedelta(hours=9)))
    # hours = hours differences with UTC

    # the encoding parameter (encoding=...) in my code is to read korean characters
    # i think it's okay to be omitted if you don't need it
    with open('temp.txt', 'w', encoding="utf-8") as f:
        f.write(f'Put any message here to notify people who send you the suggestion RT\
        \n\nRetweeted at {rttime.strftime("%Y-%m-%d %H:%M")}. Thank you for the suggestion.')
    with open('temp.txt','r', encoding="utf-8") as f:
        api.send_direct_message(recipient_id=dmsender, text=f.read())
    print('Finished.')
    return
    