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

from datetime import datetime

# Globals
SLEEPTIME = 6
MAXCOUNT = 30
CURRENTCOUNT = 0
ALLOWEDCHARS = string.ascii_letters + string.punctuation

TODAYNOW = datetime.now()

PROCESSED=0

#### LOGGING SETUP ### #
LOGLEVEL = logging.INFO
#LOGLEVEL = logging.DEBUG
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

        submission_time = datetime.fromtimestamp(submission.created_utc)
        timeago = TODAYNOW - submission_time
        daysago = timeago.days

        if submission.author == settings.REDDIT_USERNAME and daysago > settings.DELETE_AFTER_DAYS:
            logger.info('+PROCESSING submission: age=%s %s %s user=%s http://reddit.com%s' % (daysago, subname, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submission.created_utc)), submission.author, submission.permalink))
            # save to history file if enabled
            if settings.ARCHIVE_SUBMISSIONS:
                logger.info("---ARCHIVING SUBMISSION")
                f = open("deleted_submisison_archive.txt","a")
                f.write('%s http://reddit.com%s %s %s %s' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submission.created_utc)), submission.permalink, submission.title, submission.selftext, submission.url))
                f.close()
            logger.debug('---DELETE')
            submission.delete()
            PROCESSED=1
            return True
        else:
            logger.debug('+KEEP submission: age=%s %s %s user=%s http://reddit.com%s' % (daysago, subname, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submission.created_utc)), submission.author, submission.permalink))
            return False

    except Exception:
        logger.exception('Unknown Exception in process_submission id=%s, the subreddit is probably banned/deleted.' % submission.id)
        return True


def process_comment(comment):

    try:
        if comment.author is None:
            logger.info('-already deleted comment: %s http://reddit.com%s %s' % (comment.id, comment.permalink, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment.created_utc))))
            return True

        comment_time = datetime.fromtimestamp(comment.created_utc)
        timeago = TODAYNOW - comment_time
        daysago = timeago.days
        if comment.author == settings.REDDIT_USERNAME and daysago > settings.DELETE_AFTER_DAYS:
            logger.info('+PROCESSING comment: age=%s %s %s %s user=%s http://reddit.com%s' % (daysago,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment.created_utc)), comment.id, len(comment.body), comment.author, comment.permalink))
            # overwrite with random data
            if len(comment.body) < 100:
                size = 100
            else:
                size = len(comment.body) + 25
            # get random size
            randomsize = random.randint(50, size)
            new_text = ''.join(random.choice(ALLOWEDCHARS) for x in
                       range(randomsize))
            logger.info('---SHREDDING' % (size, randomsize, new_text))
            logger.debug('---SHRED %s/%s %s' % (size, randomsize, new_text))
            comment.edit(new_text)
            if settings.ARCHIVE_COMMENTS:
                logger.info("---ARCHIVING COMMENT")
                f = open("deleted_comment_archive.txt","a")
                f.write('%s http://reddit.com%s %s' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment.created_utc)), comment.permalink, comment.body))
                f.close()
            logger.debug('---DELETE')
            comment.delete()
            PROCESSED=1
            return True
        else:
            logger.debug('+KEEP comment: age=%s %s %s %s user=%s http://reddit.com%s' % (daysago, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment.created_utc)), comment.id, len(comment.body), comment.author, comment.permalink))
            return False

    except Exception:
        logger.exception('Unknown Exception in process_comment id=%s, the subreddit is probably banned/deleted.' % comment.id)
        return False

def process_message(message):
    message_time = datetime.fromtimestamp(message.created_utc)
    timeago = TODAYNOW - message_time
    daysago = timeago.days
    if daysago > settings.DELETE_AFTER_DAYS:
        logger.info('+DELETE message: age=%s %s %s %s %s subject=(%s) from=(%s) to=(%s)' % (daysago, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message.created_utc)), message.id, message.was_comment, len(message.body), message.subject, message.author, message.dest))
        if settings.ARCHIVE_MESSAGES:
            logger.info("---ARCHIVING MESSAGES")
            f = open("deleted_message_archive.txt","a")
            f.write('message: age=%s %s %s comment=%s subject=(%s) from=(%s) to=(%s) %s' % (daysago, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message.created_utc)), message.id, message.was_comment, len(message.body), message.subject, message.author, message.dest, message.body))
            f.close()
        message.delete()
        PROCESSED=1
    else:
        logger.debug('+KEEP message: age=%s %s %s %s %s subject=(%s) from=(%s) to=(%s)' % (daysago, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message.created_utc)), message.id, message.was_comment, len(message.body), message.subject, message.author, message.dest))
        return False
 


#### MAIN PROCEDURE ####

def run_bot():

    reddit = praw.Reddit(user_agent='autobots, more than meets the eye'
                         , client_id=settings.REDDIT_CLIENT_ID,
                         client_secret=settings.REDDIT_CLIENT_SECRET,
                         username=settings.REDDIT_USERNAME,
                         password=settings.REDDIT_PASSWORD)

    reddit.validate_on_submit = True
    logger.info('Start bot - Delete after %s days' % settings.DELETE_AFTER_DAYS)

    # create db tables if needed

    logger.debug('Create DB tables if needed')
    create_db()

    while True:
        CURRENTCOUNT = 0
        try:
            # process messages/pm
            logger.info('Looking for messages/pm to delete')
            for message in reddit.inbox.messages():
               process_message(message)
            
            # process comments
            logger.info('Looking for comments to delete - new')
            for comment in reddit.redditor(settings.REDDIT_USERNAME).comments.new(limit=None):
               process_comment(comment)
            logger.info('Looking for comments to delete - top')
            for comment in reddit.redditor(settings.REDDIT_USERNAME).comments.top(limit=None):
               process_comment(comment)
            logger.info('Looking for comments to delete - hot')
            for comment in reddit.redditor(settings.REDDIT_USERNAME).comments.hot(limit=None):
               process_comment(comment)
            logger.info('Looking for comments to delete - controversial')
            for comment in reddit.redditor(settings.REDDIT_USERNAME).comments.controversial(limit=None):
               process_comment(comment)
                    
            # process submissions
            logger.info('Looking for submissions to delete')
            for submission in reddit.redditor(settings.REDDIT_USERNAME).submissions.new(limit=None):
               process_submission(submission)
                    
       
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
            if PROCESSED == 1:
                sys.exit(1)
            else:
                sys.exit(0)


#### END MAIN PROCEDURE ####

#### START BOT ####

if __name__ == '__main__':
    if not settings.REDDIT_CLIENT_ID:
        logger.error('missing REDDIT_CLIENT_ID')
    else:
        run_bot()

#### END START BOT ####
