# -*- coding: utf-8 -*- 
import logging
from subscriptions.models import Subscription
from blog.models import Entry
import datetime
import feedfinder
import feedparser


def url_to_subscription(subscription_url):
    """Create a subscription object from a url —if possible"""
    if not subscription_url.startswith('http://'):
        subscription_url = 'http://%s' % subscription_url
    feeds = feedfinder.feeds(subscription_url)
    if feeds:
        subscription = Subscription()
        subscription.feed_url = feeds[0]
        data = feedparser.parse(subscription.feed_url)
        links = data.feed.get('links', [])
        if links:
            hubs = [link for link in data.feed.links if link['rel']==u'hub']
            logging.info(hubs)
            if len(hubs) > 0:
                subscription.hub = hubs[0]['href']
            else:
                subscription.hub = ''
        subscription.feed_id = data.feed.get('id', 'No ID')
        subscription.title = data.feed.get('title', 'No title')
        subscription.url = data.feed.get('link', subscription_url)
        subscription.etag = data.get('etag', '')
        updated_tuple = data.feed.get('date_parsed', None)
        if updated_tuple:
            subscription.updated = datetime.datetime(*updated_tuple[:6])
        else:
            subscription.updated = datetime.datetime.today()

    else:
        subscription = None

    return subscription


class DataFeed(object):
    """
    A basic feed object used to store fetched feeds information and entries
    """
    def __init__(self, body_or_url, etag=None, modified=None):
        self.body_or_url = body_or_url
        self.etag = etag
        self.modified = modified
        self.entries = []

    def parse(self):
        """
        Use Mark's Feedparser extraordinaire to create entries from a feed's body or
        url.
        """
        data = feedparser.parse(self.body_or_url, self.etag, self.modified)
        try:
            self.etag = data.etag
        except: pass
        try:
            self.modified = data.modified
        except:pass

        if data.bozo:
            logging.error('Bozo feed data. %s: %r',
                         data.bozo_exception.__class__.__name__,
                         data.bozo_exception)
            if (hasattr(data.bozo_exception, 'getLineNumber') and
                  hasattr(data.bozo_exception, 'getMessage')):
                line = data.bozo_exception.getLineNumber()
                logging.error('Line %d: %s', line, data.bozo_exception.getMessage())
                segment = self.request.body.split('\n')[line-1]
                logging.info('Body segment with error: %r', segment.decode('utf-8'))
            return False

        logging.info('Found %d entries', len(data.entries))
        for entry in data.entries:
            if hasattr(entry, 'content'):
                # Atom feed.
                entry_id = entry.id
                content = entry.content[0].value
                link = entry.get('link', '')
                title = entry.get('title', content[:30])
                if entry.has_key('author_detail'):
                    author = entry.author_detail.get('name', title) 
                    author_url = entry.author_detail.get('href', link)
                else:
                    author = entry.get('author', title)
                    author_url = link
                if entry.has_key('source'):
                    source_id = entry.source.id
                    source_self_links = [l.href for l in entry.source.links 
                            if l.rel=='self']
                    if source_self_links:
                        source_self_link = source_self_links[0]
                        logging.info('found self link %s' % source_self_link)
                    else:
                        source_self_link = ''
                else:
                    source_id = link
                    source_self_link = ''
            else:
                content = entry.get('description', '')
                title = entry.get('title', content[:30])
                link = entry.get('link', '')
                entry_id = (entry.get('id', '') or link or title or content)
                author = entry.get('author', title)
                author_url = link
                source_id = link
                source_self_link = ''

            updated_tuple = entry.get('updated_parsed', None)
            if updated_tuple:
                updated = datetime.datetime(*updated_tuple[:6])
            else:
                updated = datetime.datetime.today()
            published_tuple = entry.get('published_parsed', None)
            if published_tuple:
                published = datetime.datetime(*published_tuple[:6])
            else:
                published = datetime.datetime.today()

            logging.info('Found entry with title = "%s", id = "%s", '
                       'link = "%s", content = "%s"',
                       title, entry_id, link, content)
            self.entries.append(
                    Entry(
                        entry_id = entry_id,
                        body=title,
                        link=link,
                        updated = updated,
                        published = published,
                        author=author,
                        author_url = author_url,
                        source = source_self_link)
            )
        return True
