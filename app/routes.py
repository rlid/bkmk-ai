from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import render_template, redirect, url_for

from app import app, db
from app.forms import NewBookmarkForm
from app.models import Bookmark


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NewBookmarkForm()
    if form.validate_on_submit():
        url = form.url.data
        title, description = extract_title_description(url)
        domain = extract_domain(url)
        bookmark = Bookmark(url=url, title=title, description=description, domain=domain)
        db.session.add(bookmark)
        db.session.commit()
        return redirect(url_for('index'))
    bookmarks = Bookmark.query.order_by(Bookmark.timestamp.desc()).all()
    return render_template('index.html', form=form, bookmarks=bookmarks)


def extract_title_description(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        title = _extract_title(soup)
        description = _extract_description(soup)

        return title or url, description or 'No Description'
    except Exception as e:
        print('0', e)
        return url, 'No Description'


def _extract_title(soup):
    try:
        title_tag = soup.find('shreddit-title')
        if title_tag and 'title' in title_tag.attrs:
            return title_tag['title'].strip()
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        return None
    except Exception as e:
        print('1', e)
        return None


def _extract_description(soup):
    try:
        description_tag = soup.find('meta', attrs={'name': 'description'})
        if description_tag and 'content' in description_tag.attrs:
            description = description_tag['content'].strip()
            return description
        return None
    except Exception as e:
        print('2', e)
        return None


def extract_domain(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain
    except Exception as e:
        return url


@app.template_filter('format_time')
def format_time(timestamp):
    current_time = datetime.now()
    seconds = (current_time - timestamp).total_seconds()

    if seconds < 60:
        return f'{int(seconds)} seconds ago'
    elif seconds < 3600:
        minutes = seconds / 60
        return f'{int(minutes)} minutes ago'
    elif seconds < 86400:
        hours = seconds / 3600
        return f'{int(hours)} hours ago'
    else:
        days = seconds / 86400
        return f'{int(days)} days ago'


@app.route('/initdb')
def initdb():
    db.drop_all()
    db.create_all()
    return {'message': 'database is initialised'}
