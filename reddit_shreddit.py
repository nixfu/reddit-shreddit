#!/usr/bin/env python3

import time
import logging.handlers
import logging
import sys
import os
import sqlite3
import random
import string
import csv
import praw
import settings

# Globals
SLEEPTIME = 60
MAXCOUNT = 30
CURRENTCOUNT = 0
ALLOWEDCHARS = string.ascii_letters + string.punctuation

#### LOGGING SETUP ### #
LOGLEVEL = logging.INFO
# LOGLEVEL = logging.DEBUG
logger = logging.getLogger('bot')
logger.setLevel(LOGLEVEL)
log_formatter = logging.Formatter('%(levelname)-8s:%(asctime)s:%(lineno)4d - %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
logger.addHandler(log_stderrHandler)
log_fileHandler = logging.handlers.TimedRotatingFileHandler('bot.log', when='d', interval=2, backupCount=10)
log_fileHandler.setFormatter(log_formatter)
logger.addHandler(log_fileHandler)
#### END LOGGING SETUP ### #


def create_db():

    # create database tables if don't already exist
    try:
        con = sqlite3.connect('processed.db')
        ccur = con.cursor()
        ccur.execute('CREATE TABLE IF NOT EXISTS processed (id TEXT, epoch INTEGER)')
        con.commit()
    except sqlite3.Error as SqlError:
        logger.error('Error2 {}:'.format(SqlError.args[0]))
        sys.exit(1)
    finally:
        if con:
            con.close()


def check_processed_sql(messageid):
    logger.debug('Check processed for id=%s' % messageid)
    try:
        con = sqlite3.connect('processed.db')
        qcur = con.cursor()
        qcur.execute("SELECT id FROM processed WHERE id=?", (messageid,))
        row = qcur.fetchone()
        if row:
            return True
        else:
            icur = con.cursor()
            insert_time = int(round(time.time()))
            icur.execute('''INSERT INTO processed VALUES(?, ?)''',
                         [messageid, insert_time])
            con.commit()
            return False
    except sqlite3.Error as SqlError:
        logger.error('SQL Error: %s' % SqlError)
    finally:
        if con:
            con.close()


def process_submission(submission):

    try:
        subname = str(submission.subreddit.display_name).lower()
        if submission.author is None:
            logger.info('-already deleted submission: %s %s user=%s http://reddit.com%s' % (subname, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submission.created_utc)), submission.author, submission.permalink))
            return True
        if submission.author == settings.REDDIT_USERNAME:
            logger.info('+PROCESSING submission: %s %s user=%s http://reddit.com%s' % (subname, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submission.created_utc)), submission.author, submission.permalink))
            logger.debug('---DELETE')
            submission.delete()
    except Exception:
        logger.exception('Unknown Exception in process_submission id=%s, the subreddit is probably banned/deleted.' % submission.id)
        return True


def process_comment(comment):

    try:
        if comment.author is None:
            logger.info('-already deleted comment: %s http://reddit.com%s %s' % (comment.id, comment.permalink, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment.created_utc))))
            return True
        if comment.author == settings.REDDIT_USERNAME:
            logger.info('+PROCESSING comment: %s %s %s user=%s http://reddit.com%s' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment.created_utc)), comment.id, len(comment.body), comment.author, comment.permalink))

        # overwrite with random data

        if len(comment.body) < 100:
            size = 100
        else:
            size = len(comment.body) + 25

        # get random size

        randomsize = random.randint(50, size)
        new_text = ''.join(random.choice(ALLOWEDCHARS) for x in
                           range(randomsize))
        logger.debug('---SHRED %s/%s %s' % (size, randomsize, new_text))
        comment.edit(new_text)
        logger.debug('---DELETE')
        comment.delete()
    except Exception:
        logger.exception('Unknown Exception in process_comment id=%s, the subreddit is probably banned/deleted.' % comment.id)
        return True


#### MAIN PROCEDURE ####

def run_bot():

    reddit = praw.Reddit(user_agent='autobots, more than meets the eye'
                         , client_id=settings.REDDIT_CLIENT_ID,
                         client_secret=settings.REDDIT_CLIENT_SECRET,
                         username=settings.REDDIT_USERNAME,
                         password=settings.REDDIT_PASSWORD)

    reddit.validate_on_submit = True
    logger.info('Start bot')

    # create db tables if needed

    logger.debug('Create DB tables if needed')
    create_db()

    saved_comments_list = []
    delete_comments_list = []
    saved_posts_list = []
    delete_posts_list = []

    if os.path.isfile('saved_comments.csv'):
        logger.info('Read saved_comments.csv')
        with open('saved_comments.csv', newline='', encoding='utf-8') as fs:
            saved_reader = csv.reader(fs)
            for saved_row in saved_reader:
                if 'id' in saved_row[0]:  # skip heading row
                    continue
                saved_comments_list.append(saved_row[0])
    else:
        logger.info('No saved_comments.csv file, skipping.')

    if os.path.isfile('comments.csv'):
        logger.info('Read comments.csv')
        with open('comments.csv', newline='', encoding='utf-8') as fd:
            del_reader = csv.reader(fd)
            for del_row in del_reader:
                if 'id' in del_row[0]:  # skip heading row
                    continue
                delete_comments_list.append(del_row[0])
    else:
        logger.info('No comments.csv file, Skipping.')

    if os.path.isfile('saved_posts.csv'):
        logger.info('Read saved_posts.csv')
        with open('saved_posts.csv', newline='', encoding='utf-8') as fs:
            saved_reader = csv.reader(fs)
            for saved_row in saved_reader:
                if 'id' in saved_row[0]:  # skip heading row
                    continue
                saved_posts_list.append(saved_row[0])
    else:
        logger.info('No saved_posts.csv file, skipping.')

    if os.path.isfile('posts.csv'):
        logger.info('Read posts.csv')
        with open('posts.csv', newline='', encoding='utf-8') as fd:
            del_reader = csv.reader(fd)
            for del_row in del_reader:
                if 'id' in del_row[0]:  # skip heading row
                    continue
                delete_posts_list.append(del_row[0])
    else:
        logger.info('No posts.csv file, Skipping.')

    while True:
        CURRENTCOUNT = 0
        try:

            # process comments

            logger.info('Looking for comments to delete')
            for comment_id in delete_comments_list:
                if comment_id in saved_comments_list:
                    logger.debug('Keeping saved comment: %s'
                                 % comment_id)
                    continue
                comment = reddit.comment(comment_id)
                if comment is None:
                    break
                elif check_processed_sql(str(comment_id)):
                    continue
                else:
                    process_comment(comment)
                    CURRENTCOUNT += 1
                    logger.debug('count=%s' % CURRENTCOUNT)
                    if CURRENTCOUNT > MAXCOUNT:
                        logger.info('sleep for %s s', SLEEPTIME)
                        time.sleep(SLEEPTIME)
                        CURRENTCOUNT = 0

            # process posts

            logger.info('Looking for posts to delete')
            for post_id in delete_posts_list:
                if post_id in saved_posts_list:
                    logger.debug('Keeping saved Post: %s' % post_id)
                    continue
                submission = reddit.submission(id=post_id)
                if submission is None:
                    break
                elif check_processed_sql(str(post_id)):
                    continue
                else:
                    process_submission(submission)
                    CURRENTCOUNT += 1
                    logger.debug('count=%s' % CURRENTCOUNT)
                    if CURRENTCOUNT > MAXCOUNT:
                        logger.info('sleep for %s s', SLEEPTIME)
                        time.sleep(SLEEPTIME)
                        CURRENTCOUNT = 0
        except KeyboardInterrupt:
        # Allows the bot to exit on ^C, all other exceptions are ignored
            CURRENTCOUNT = 0
            logger.info('Keyboard exit')
            break
        except Exception as ExError:
            logger.error('Exception %s', ExError, exc_info=True)
            CURRENTCOUNT = 0
            logger.info('sleep for %s s', SLEEPTIME)
            time.sleep(SLEEPTIME)

        if CURRENTCOUNT == 0:
            logger.info('Nothing to do. Exit')
            sys.exit(0)


#### END MAIN PROCEDURE ####

#### START BOT ####

if __name__ == '__main__':
    if not settings.REDDIT_CLIENT_ID:
        logger.error('missing REDDIT_CLIENT_ID')
    else:
        run_bot()

#### END START BOT ####
