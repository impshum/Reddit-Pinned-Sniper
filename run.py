import praw
from time import sleep
import schedule
import configparser
import pickledb
from requests import get
from requests.exceptions import ConnectionError


def wait_until_online(timeout, slumber):
    offline = 1
    t = 0
    while offline:
        try:
            r = get('https://google.com', timeout=timeout).status_code
        except ConnectionError:
            r = None
        if r == 200:
            offline = 0
        else:
            t += 1
            if t > 3:
                quit()
            else:
                print('BOT OFFLINE')
                sleep(slumber)


def do_db(db, id, sub):
    if not db.exists(id):
        db.set(id, sub)
        db.dump()
        return True


def sniper(reddit, main_subreddit, target_subreddits, send_replies, crosspost, test_mode, db):
    wait_until_online(10, 3)
    for target_subreddit in target_subreddits:
        for submission in reddit.subreddit(target_subreddit).new(limit=None):
            if submission.stickied:
                title = submission.title
                selftext = submission.selftext
                if not test_mode:
                    if do_db(db, submission.id, target_subreddit):
                        if crosspost:
                            submission.crosspost(
                                subreddit=main_subreddit, send_replies=send_replies)
                        else:
                            reddit.subreddit(main_subreddit).submit(
                                title, selftext=selftext, send_replies=send_replies)
                        print(f'r/{target_subreddit} → {title[0:80]}')


def main():
    db = pickledb.load('history.db', False)
    config = configparser.ConfigParser()
    config.read('conf.ini')
    main_subreddit = config['SETTINGS']['main_subreddit']
    target_subreddits = config['SETTINGS']['target_subreddits']
    target_subreddits = [x.strip() for x in target_subreddits.split(',')]
    print(target_subreddits)
    quit()
    send_replies = config['SETTINGS'].getboolean('send_replies')
    crosspost = config['SETTINGS'].getboolean('crosspost')
    test_mode = config['SETTINGS'].getboolean('test_mode')
    reddit = praw.Reddit(
        username=config['REDDIT']['reddit_user'],
        password=config['REDDIT']['reddit_pass'],
        client_id=config['REDDIT']['reddit_client_id'],
        client_secret=config['REDDIT']['reddit_client_secret'],
        user_agent='Pinned Sniper (by u/impshum)'
    )

    if test_mode:
        print('\nTEST MODE\n')

    sniper(reddit, main_subreddit, target_subreddits,
           send_replies, crosspost, test_mode, db)

    schedule.every().hour.do(sniper, reddit=reddit, main_subreddit=main_subreddit, target_subreddits=target_subreddits,
                             send_replies=send_replies, crosspost=crosspost, test_mode=test_mode, db=db)

    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    main()
