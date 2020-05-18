import logging
from collections import OrderedDict

import pandas
import requests
import re
import json
import time

from bs4 import BeautifulSoup


def json_to_obj(filename):
    """Extracts data from JSON file and saves it on Python object
    """
    obj = None
    with open(filename) as json_file:
        obj = json.loads(json_file.read())
    return obj


def make_login(session, base_url, credentials):
    """Returns a Session object logged in with credentials.
    """
    # login_form_url = '/login/device-based/regular/login/?login_attempt=1&lwv=110'

    login_form_url = '/login/device-based/regular/login/?refsrc=https%3A' \
                     '%2F%2Fmobile.facebook.com%2Flogin%2Fdevice-based%2Fedit-user%2F&lwv=100'

    params = {'email': credentials['email'], 'pass': credentials['pass']}

    while True:
        time.sleep(3)
        logged_request = session.post(base_url + login_form_url, data=params)


        if logged_request.ok:

            logging.info('[*] Logged in.')
            break

def get_bs(session, url):
    """Makes a GET requests using the given Session object
    and returns a BeautifulSoup object.
    """
    print(url)
    r = None
    while True:
        r = session.get(url)
        time.sleep(3)
        if r.ok:
            break
    return BeautifulSoup(r.text, 'lxml')


def scrape_post(session, base_url, post_url):
    """Goes to post URL and extracts post data.
    """
    post_data = OrderedDict()

    post_bs = get_bs(session, base_url + post_url)
    time.sleep(5)

    # Here we populate the OrderedDict object
    post_data['url'] = post_url

    try:
        post_text_element = post_bs.find('div', id='u_0_0').div
        string_groups = [p.strings for p in post_text_element.find_all('p')]
        strings = [repr(string) for group in string_groups for string in group]
        post_data['text'] = strings
    except Exception:
        post_data['text'] = []

    return dict(post_data)

def posts_completed(scraped_posts, limit):
    """Returns true if the amount of posts scraped from
    profile has reached its limit.
    """
    if len(scraped_posts) == limit:
        return True
    else:
        return False


def crawl_profile(session, base_url, profile_url, post_limit):
    """Goes to profile URL, crawls it and extracts posts URLs.
    """
    profile_bs = get_bs(session, profile_url)
    n_scraped_posts = 0
    scraped_posts = list()
    posts_id = None
    posts = None

    while n_scraped_posts < post_limit:
        try:
            posts_id = 'recent'
            posts = profile_bs.find('div', id=posts_id).div.div.contents
        except Exception:
            # posts_id = 'structured_composer_async_container'
            # posts = profile_bs.find('div', id=posts_id).div.div.contents
            posts_id = None

        if(posts_id==None):
            break
        posts_urls = [a['href'] for a in profile_bs.find_all('a', text='Full Story')]

        for post_url in posts_urls:
            # print(post_url)
            try:
                post_data = scrape_post(session, base_url, post_url)
                scraped_posts.append(post_data)
            except Exception as e:
                logging.info('Error: {}'.format(e))
            n_scraped_posts += 1
            if posts_completed(scraped_posts, post_limit):
                break

        show_more_posts_url = None
        if not posts_completed(scraped_posts, post_limit):
            show_more_posts_url = profile_bs.find('div', id=posts_id).next_sibling.a['href']
            profile_bs = get_bs(session, base_url + show_more_posts_url)
            time.sleep(3)
        else:
            break
    return scraped_posts

def save_data(data):
    """Converts data to JSON.
    """
    with open('profile_posts_data.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    # base_url = 'https://www.facebook.com/'
    base_url = 'https://mobile.facebook.com'
    session = requests.session()

    # Extracts credentials for the login and all of the profiles URL to scrape
    credentials = json_to_obj('/home/ankita/PycharmProjects/Demo/credentials.json')
    profiles_urls = json_to_obj('/home/ankita/PycharmProjects/Demo/profile_urls.json')
    print(credentials)

    make_login(session, base_url, credentials)

    posts_data = None
    for profile_url in profiles_urls:
        posts_data = crawl_profile(session, base_url, profile_url, 40)

    if(len(posts_data)==0):
        logging.info('No such page exits')
    else:
        logging.info('[!] Scraping finished. Total: {}'.format(len(posts_data)))
        logging.info('[!] Saving.')
        save_data(posts_data)




