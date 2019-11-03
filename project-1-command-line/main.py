import argparse
import logging
import datetime
import csv
from requests.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError

# local imports
from common import config
import news_page_objects as news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _news_scraper(news_sites_uid):
    host = config()['news_sites'][news_sites_uid]['url']
    logging.info('Beginning scraper for {}'.format(host))
    homepage = news.HomePage(news_sites_uid, host)
    articles = []

    for link in homepage.articles_links:
        print(link)
        article = _fetch_article(news_sites_uid, host, link)

        if article:
            articles.append(article)
    _save_articles(news_sites_uid, articles)
    print(len(articles))


def _save_articles(news_sites_uid, articles):
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    out_file_name = '{news_sites_uid}_{datatime}_articles.csv'.format(
        news_sites_uid=news_sites_uid,
        datatime=now
    )
    csv_headers = list(filter(lambda property: not property.startswith('_'), dir(articles[0])))

    with open(out_file_name, mode='w+') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        for article in articles:
            row = [str(getattr(article, prop)) for prop in csv_headers]
            writer.writerow(row)


def _fetch_article(news_sites_uid, host, link):
    logger.info('Start fetching article at {}'.format(link))
    article = None
    try:
        article = news.ArticlePage(news_sites_uid, link)
    except (HTTPError, MaxRetryError) as e:
        logger.error('The article coudn\'t be fetched')

    if article and not article.body:
        logger.warning('There isn\'t a body in this page.   ')
        return None

    return article


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    news_sites_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_sites',
                        help='The news site that you want to scrape',
                        type=str,
                        choices=news_sites_choices)

    args = parser.parse_args()
    _news_scraper(args.news_sites)
