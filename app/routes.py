import json
import re
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import render_template, redirect, url_for, request
from openai import OpenAI
from sqlalchemy import func, distinct, not_, desc

from app import app, db
from app.forms import NewLinkForm, DeleteLinkForm
from app.models import Link, Tag, LinkTag


@app.route('/delete/<int:link_id>', methods=['POST'])
def delete_link(link_id):
    form = DeleteLinkForm()
    if form.validate_on_submit():
        link = Link.query.get_or_404(link_id)
        db.session.delete(link)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    tags = re.findall(r'\w+', request.args.get("tags", ""))
    seen = set()
    tag_ids_to_filter = [tag.lower() for tag in tags if not (tag.lower() in seen or seen.add(tag.lower()))]
    if tag_ids_to_filter:
        link_query = Link.query.join(
            LinkTag, LinkTag.link_id == Link.id
        ).filter(
            LinkTag.tag_id.in_(tag_ids_to_filter)
        ).group_by(
            Link
        ).having(
            func.count(distinct(LinkTag.tag_id)) == len(tag_ids_to_filter)
        ).order_by(Link.timestamp.desc())
        tags_in_filter = Tag.query.filter(Tag.id.in_(tag_ids_to_filter)).all()
    else:
        link_query = Link.query.order_by(Link.timestamp.desc())
        tags_in_filter = []

    link_subquery = link_query.subquery()
    tags_not_in_filter = db.session.query(
        Tag,
        func.count(LinkTag.link_id).label('link_tag_count')
    ).join(
        LinkTag,
        LinkTag.tag_id == Tag.id
    ).join(
        link_subquery,
        link_subquery.c.id == LinkTag.link_id
    ).filter(
        not_(Tag.id.in_(tag_ids_to_filter))
    ).group_by(
        Tag
    ).order_by(
        desc('link_tag_count')
    ).all()

    form = NewLinkForm()
    if form.validate_on_submit():
        url = form.url.data
        title, description = extract_title_description(url)
        domain = extract_domain(url)

        link = Link(url=url, title=title, description=description, domain=domain)
        db.session.add(link)
        tag_names = generate_tags(url, title, description)
        add_tags(link, tag_names)

        db.session.commit()
        return redirect(url_for('index'))
    links = link_query.all()

    delete_form = DeleteLinkForm()

    return render_template(
        'index.html',
        form=form,
        links=links,
        delete_form=delete_form,
        tags_in_filter=tags_in_filter,
        tags_not_in_filter=tags_not_in_filter
    )


def _add_tag(link, tag_name):
    tag = Tag.query.get(tag_name.lower())
    if tag is None:
        tag = Tag(id=tag_name.lower(), name=tag_name)
        db.session.add(tag)
    link_tag = link.link_tags.filter_by(tag=tag).first()
    if link_tag is None:
        link_tag = LinkTag(link=link, tag=tag)
        db.session.add(link_tag)


def add_tags(link, tag_names):
    for tag_name in tag_names:
        _add_tag(link, tag_name)


def extract_title_description(url):
    try:
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
        }
        response = requests.get(url, headers=headers)
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
        # Open Graph description
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        if og_description:
            return og_description['content'].strip()

        # Twitter card description
        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_description:
            return twitter_description['content'].strip()

        # Standard meta tag with name='description'
        description_tag = soup.find('meta', attrs={'name': 'description'})
        if description_tag:
            return description_tag['content'].strip()

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


def generate_tags(url, title, description):
    prompt = f'''
    List 3 to 5 Reddit subreddits or online communities the below link in brackets most likely to appear in, output as
    a JSON list with up to 5 child objects, each child object has exactly 2 properties 'name' and 'probability',
    do not include the prefix "r/"
    (
    URL: {url}
    Title: {title}
    Description: {description}
    )
    '''
    client = OpenAI()

    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        temperature=0,  # this is the degree of randomness of the model's output
    )
    response_text = response.choices[0].message.content
    return [x['name'] for x in json.loads(response_text) if x['probability'] >= 0]


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
