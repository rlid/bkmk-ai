from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import render_template, redirect, url_for, flash
from flask_login import login_user

from app import app, db
from app.forms import NewBookmarkForm, DeleteBookmarkForm, LoginForm
from app.models import Bookmark, User


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)


@app.route('/delete/<int:bookmark_id>', methods=['POST'])
def delete_bookmark(bookmark_id):
    form = DeleteBookmarkForm()
    if form.validate_on_submit():
        bookmark = Bookmark.query.get_or_404(bookmark_id)
        db.session.delete(bookmark)
        db.session.commit()
    return redirect(url_for('index'))


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

    delete_form = DeleteBookmarkForm()
    return render_template('index.html', form=form, bookmarks=bookmarks, delete_form=delete_form)


def extract_title_description(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        title = _extract_title(soup)
        description = _extract_description(soup)

        return title or url, description or 'No Description'
    except Exception as e:
        return url, 'No Description'


def _extract_title(soup):
    try:
        # Custom tag 'shreddit-title' for Reddit
        reddit_title = soup.find('shreddit-title')
        if reddit_title:
            return reddit_title['title'].strip()

        # Standard HTML title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)

        # Open Graph title
        og_title = soup.find('meta', attrs={'property': 'og:title', 'content': True})
        if og_title:
            return og_title['content'].strip()

        # Twitter-specific title
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title', 'content': True})
        if twitter_title:
            return twitter_title['content'].strip()

        # Schema.org title
        schema_title = soup.find('meta', attrs={'itemprop': 'name', 'content': True})
        if schema_title:
            return schema_title['content'].strip()

        # HTML5 microdata
        microdata_title = soup.find(attrs={'itemprop': 'headline'})
        if microdata_title:
            return microdata_title.get_text(strip=True)

        # Dublin Core title
        dc_title = soup.find('meta', attrs={'name': 'DC.title', 'content': True})
        if dc_title:
            return dc_title['content'].strip()

        # h1 tags
        h1_title = soup.find('h1')
        if h1_title:
            return h1_title.get_text(strip=True)

        # Alternative meta tag for title
        alt_meta_title = soup.find('meta', attrs={'name': 'title', 'content': True})
        if alt_meta_title:
            return alt_meta_title['content'].strip()

        # Fallback to None if no title is found
        return None
    except Exception as e:
        return None


def _extract_description(soup):
    try:
        # Standard meta tag with name='description'
        description_tag = soup.find('meta', attrs={'name': 'description'})
        if description_tag:
            return description_tag['content'].strip()

        # Open Graph description
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        if og_description:
            return og_description['content'].strip()

        # Twitter card description
        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_description:
            return twitter_description['content'].strip()

        # Additional meta tag checks
        additional_meta_tags = ['og:title', 'twitter:title', 'keywords']
        for tag in additional_meta_tags:
            result = soup.find('meta', attrs={'property': tag, 'name': tag})
            if result:
                return result['content'].strip()

        # HTML tags like p or div with specific IDs or classes (this is highly specific to the website)
        html_tags = [('p', 'description'), ('div', 'description'), ('section', 'description')]
        for tag, class_name in html_tags:
            result = soup.find(tag, {'class': class_name})
            if result:
                return result.get_text().strip()

        return None
    except Exception as e:
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
