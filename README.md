# reddit-shreddit
Program to delete ALL of your Reddit user submissions and comments history on Reddit, also a daily shredding program to keep your amount of saved user data low.  (See #8 below for the limitations that apply)

Using programs which parse through the user history prestented by the reddit website/API and reddit.com/user/<myusername> are limted to only the last 1000 items max and will never see anything older than that.  The process documented here is the only known method to delete your entire Reddit history from day one forward to now.

*NOTE: This is a python3 program, and requires installing python3, and [installing the required python library (PRAW)](https://praw.readthedocs.io/en/latest/getting_started/installation.html).  You should have some knowledge of how to run python programs before attempting this.*

## Would you like to delete your ENTIRE post and comment history on Reddit?

#### Here is the process:

##### 1. Request a complete data archive download of your user data from Reddit
 
 To request a complete copy of your entire Reddit user data, [follow the process on this page](https://reddit.zendesk.com/hc/en-us/articles/360043048352-How-do-I-request-a-copy-of-my-Reddit-data-and-information-) and Reddit will process the request and in a few days Reddit will send an archive(zip) of all your Reddit data to your reddit account or to your verified email address.
 
##### 2. Download a copy of reddit-shreddit to your own system and setup the requirements.

- Install Python3 if you have not done so.
- Install the PRAW python libary, via pip/pip3.  see: https://praw.readthedocs.io/en/latest/getting_started/installation.html
- Download a copy of reddit-shreddit by clicking on the green CODE button at the top right, and pulling down to download ZIP.

 
##### 3. Once the archive of your history data is recieved from Reddit, copy the following files from the Reddit data archive recieved to the same directroy as where you will be running reddit-shreddit.
 
 * **comments.csv** - if you want to keep some recent history go the bottom of the file and delete anything newer that you want to keep
 * **posts.csv** - same-as-above, remove any you want to keep, such as a some recent activity
 * **saved_comments.csv** (optional) - if this file is present it will skip deleting any comments you "saved" on Reddit
 * **saved_posts.csv** (optional) - if this file is present it will skip deleteing any posts that you "saved" on Reddit

If any of the files are missing, it will just continue with what it has, so for instance if you just wanted to delete comments, just put the comments.csv file in the directory, and it will then have no posts to process and skip that step.
 
##### 4. Create a Reddit API authorization key for your account

Go to your [Reddit user account app preferences](https://www.reddit.com/prefs/apps). 

Click the "Create app" or "Create another app" button. Fill out the form like so:

* name: **shreddit**
* App type: Choose the SCRIPT option
* description: You can leave this blank
* about url: You can leave this blank
* redirect url: **http://127.0.0.1**

THEN, hit the "create app" button. 

Make note of the client ID and client secret. The required information will look something like this.

- Client ID: Is, LOCATED under the script name on the top left.
- Cient secret:  Shown in the "Secret" field of the box.

Note: You should NEVER post your client secret (or your reddit password) in public. If you create a bot, you should take steps to ensure that the bot's password and the app's client secret are secured against digital theft. The client IDs, secrets, tokens and passwords used here are, obviously, fake and invalid.

##### 5. Create a settings.py file with the Reddit secrets

Copy the settings.py-EXAMPLE file to settings.py.

Replace the XXXXXX's with your actual Application ClientID/ClientSecret, and Reddit Username/Password.

##### 6. RUN reddit_shreddit.py and enjoy the show

The program will go through every comment and first fill them in with random characters and re-saving to overwrite, and then it will delete the comment.

- If the saved_comments.csv file is present, it will skip any comments listed in that file that were marked "saved" by the user on Reddit.
- The program keeps track of each comment it has already processed in a database file.  So it can be ran over again, and will skip items it has already processed.

After it processes all comments in the comments.csv file, it will delete any posts listed in the posts.csv file.

- If the saved_posts.csv file is present, it will skip any posts listed in that file that were marked "saved" by the user on Reddit.
- The program keeps track of each comment it has already processed in a database file.  So it can be ran over again, and will skip items it has already processed.


In order to be polite, the processing does 30 items at a time, and then sleeps for 60 seconds before proceding with the next group.  

It may take several hours to delete all of your entire comment and post history. 

Rough estimate of time it might take.  Assume it takes 90 seconds to process each set of 30 items, there are 86400 in a day / 90 = 960 groups * 30 items = can process about 28800 items per day.

##### 7. BONUS - delete your user data from appearing in the popular databases used to see deleted/removed posts

You can request that your account data all be removed, and never stored again in the Pushshift.io database.  This is the database used by services such as removeddit.com and others that normally archive reddit data and allow the viewing of deleted reddit content.

To request your data be deleted from Pushshift.io, go here and follow the directions to add your request to the current "Data Deletion Request Megathread" in the pushshift subreddit: https://www.reddit.com/r/pushshift/

##### 8. THE BAD NEWS - The bad news is that deleting content on Reddit does not "totally" delete your records in Reddits internal database.

I used this process to delete 13 years worth of comments and submissions for my account.  I waited a few months, and the requested a new copy of my Reddit data.  

What I found:

- Comments -- Yes all the comments no longer appeared on the reddit website when viewing them, but my Reddit data archive still contained the links to every comment.  HOWEVER, the shredding(random) data did replace the actual content in Reddits database.   So while reddit in their internal database still has a history of where you commented, this process a) shreds the contents of all your comments, and it b) deletes the comment from the Reddit website so no one else can ever view it or see that you commented.

- Posts/Submissions -- The submissions still are contained in your Reddit history.  However, anyone viewing any of the submissions will see that they were deleted and no longer show who submitted them.


# DAILY SHREDDING

Included is also a program for daily shredding, called daily_shreddit.py.  You can run this program as a daily cron job and it will automatically delete and shred any messages/pm's, comments, and submissions that are older than the DELETE_AFTER_DAYS (> days old) in the settings.py.    
