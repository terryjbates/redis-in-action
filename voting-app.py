#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Terry Bates on 2013-02-08.
Copyright (c) 2013 http://the-awesome-python-blog.posterous.com. All rights reserved.
"""


import redis
import sys
import os
import time

ONE_WEEK_IN_SECONDS = 7 * 86400
VOTE_SCORE = 432
ARTICLES_PER_PAGE = 25

def article_vote(conn, user, article):
    cutoff = time.time() - ONE_WEEK_IN_SECONDS
    if conn.zscore('time:', article) < cutoff:
        return
    article_id = article.partition(':')[-1]
    if conn.sadd('voted:' + article_id, user):
        conn.zincrby('score:', article, VOTE_SCORE)
        conn.hincrby(article, 'votes', 1)

def post_article(conn, user, title, link):
    article_id = str(conn.incr('article:'))
    voted = 'voted:' + article_id
    conn.sadd(voted, user)
    conn.expire(voted, ONE_WEEK_IN_SECONDS + 1)
    
    now = time.time()
    article = 'article:' + article_id
    conn.hmset(article, {
        'title': title,
        'link': link,
        'poster': user,
        'time': now,
        'votes': 1,
    })
    
    conn.zadd('score:', article, now + VOTE_SCORE)
    conn.zadd('time:', article, now)
    
    return article_id

def get_articles(conn, page, order='score:'):
    start = max(page-1, 0) * ARTICLES_PER_PAGE
    end = start + ARTICLES_PER_PAGE - 1
    ids = conn.zrevrange(order, start, end)
    articles = []
    for id in ids:
        article_data = conn.hgetall(id)
        article_data['id'] = id
        articles.append(article_data)

    return articles
def add_remove_groups(conn, article_id, to_add=[], to_remove=[]):
    article = 'article' + article_id
    for group in to_add:
        conn.sadd('group:' + group, article)
    for group in to_remove:
        conn.srem('group:' + group, article)
def get_group_articles(conn, group, page, order='score'):
    key = order + group
    if not conn.exists(key):
        conn.zinterstore(key,
            ['group:' + group, order],
            aggregate = 'max',
        )
        conn.expire(key, 60)
    return get_articles(conn, page, key)
    
def main():
    # Open up connection to local redis instance
    conn = redis.Redis()


if __name__ == '__main__':
    main()

