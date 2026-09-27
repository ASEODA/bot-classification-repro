#!/usr/bin/env python3
"""Rebuild the analysis SQLite dataset from the original fox8 NDJSON.gz file.
--check compares every user and tweet field, in input order, with an existing DB.
"""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import sqlite3

SCHEMA = '''
CREATE TABLE users (user_id TEXT PRIMARY KEY, label TEXT, dataset TEXT, tweet_count INTEGER);
CREATE TABLE tweets (
 tweet_id TEXT, user_id TEXT, label TEXT, created_at TEXT, text TEXT,
 is_retweet INTEGER, is_quote INTEGER, is_reply INTEGER,
 retweet_count INTEGER, favorite_count INTEGER,
 hashtag_count INTEGER, url_count INTEGER, mention_count INTEGER, source TEXT);
CREATE INDEX idx_tweets_user ON tweets(user_id);
CREATE INDEX idx_tweets_label ON tweets(label);
CREATE INDEX idx_tweets_time ON tweets(created_at);
'''

def rows(account):
    uid, label = str(account['user_id']), account['label']
    tweets = account['user_tweets']
    user = (uid, label, account['dataset'], len(tweets))
    output = []
    for tweet in tweets:
        ent = tweet.get('entities') or {}
        created = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y').strftime('%Y-%m-%d %H:%M:%S')
        text = tweet.get('full_text', tweet.get('text', ''))
        output.append((str(tweet.get('id_str') or tweet['id']), uid, label, created, text,
                       int('retweeted_status' in tweet or text.startswith('RT @')), int(bool(tweet.get('is_quote_status'))),
                       int(tweet.get('in_reply_to_status_id') is not None),
                       tweet.get('retweet_count', 0), tweet.get('favorite_count', 0),
                       len(ent.get('hashtags', [])), len(ent.get('urls', [])),
                       len(ent.get('user_mentions', [])), tweet.get('source', '')))
    return user, output

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('ndjson_gz',type=Path);ap.add_argument('sqlite',type=Path)
    ap.add_argument('--check',action='store_true');a=ap.parse_args()
    if not a.check and a.sqlite.exists():raise FileExistsError(a.sqlite)
    con=sqlite3.connect(a.sqlite.as_uri()+'?mode=ro',uri=True) if a.check else sqlite3.connect(a.sqlite)
    if a.check:
        users=iter(con.execute('SELECT * FROM users ORDER BY rowid'))
        tweets=iter(con.execute('SELECT * FROM tweets ORDER BY rowid'))
    else:con.executescript(SCHEMA)
    n_users=n_tweets=0
    merged_users = {}
    with gzip.open(a.ndjson_gz,'rt',encoding='utf-8') as f:
        for line in f:
            user, data=rows(json.loads(line));n_users+=1;n_tweets+=len(data)
            uid, label, dataset, count = user
            merged_users[uid] = (uid, label, dataset, merged_users.get(uid, ('', '', '', 0))[3] + count)
            if a.check:
                for row in data:
                    ref=next(tweets)
                    if row!=ref:raise ValueError(f'Tweet {row[0]} differing columns: {[i for i in range(len(row)) if row[i]!=ref[i]]}')
            else:
                con.executemany('INSERT INTO tweets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',data)
    if a.check:
        for uid, user in merged_users.items():
            if user != next(users): raise ValueError(f'User mismatch at UID {uid}')
        if next(users,None) is not None or next(tweets,None) is not None: raise ValueError('Extra DB rows')
    else: con.executemany('INSERT INTO users VALUES (?,?,?,?)', merged_users.values())
    if not a.check:con.commit()
    con.close();print(json.dumps({'passed':True,'source_account_rows':n_users,'users':len(merged_users),'tweets':n_tweets,'mode':'compare_all_fields' if a.check else 'rebuild'}))

if __name__=='__main__':main()
