# Externals imports
import requests
import bs4
import re
# Internal imports
from common import config

# ------- Regular expression define --------#
is_well_formed_link = re.compile(r'^https?://.+$')
is_root_path = re.compile(r'^/.+$')


class NewsPage:
    def __init__(self, news_sites_uid, url):
        self._config = config()['news_sites'][news_sites_uid]
        self._queries = self._config['queries']
        self._compiling_regex()
        self._url = url
        self._html = None
        self._visit()

    def _select(self, query_string):
        return self._html.select(query_string)

    def _select_label_a(self):
        return self._html.find_all('a')

    def _visit(self):
        response = requests.get(self._url)
        response.raise_for_status()
        self._html = bs4.BeautifulSoup(response.text, 'html.parser')

    def _general_filter_links(self, link):
        if is_well_formed_link.match(link):
            return link
        elif is_root_path.match(link):
            return '{main_url}{complement_url}'.format(
                main_url=self._url,
                complement_url=link
            )
        else:
            return ''

    def _filter_link(self, regular_ex, link):
        flag = regular_ex.match(link)
        if flag:
            return link
        else:
            return None

    def _compiling_regex(self):
        self._pattern_main = re.compile(self._config['regex']['main_page'])
        self._pattern_articles = re.compile(self._config['regex']['articles'])
        self._pattern_sub = re.compile(self._config['regex']['sub_pages'])


class HomePage(NewsPage):
    def __init__(self, news_sites_uid, url):
        super().__init__(news_sites_uid, url)

    @property
    def articles_links(self):
        links_set = set([])
        for link in self._select_label_a():
            if link and link.has_attr('href'):
                valid_link = self._filter_link(self._pattern_articles, self._general_filter_links(link.get('href')))
                if valid_link:
                    links_set.add(valid_link)
        return links_set

    @property
    def sub_cite_links(self):
        links_set = set([])
        for link in self._select_label_a():
            if link and link.has_attr('href'):
                valid_link = self._filter_link(self._pattern_sub, self._general_filter_links(link.get('href')))
                if valid_link:
                    links_set.add(valid_link)
        return links_set


class ArticlePage(NewsPage):
    def __init__(self, news_sites_uid, url):
        super().__init__(news_sites_uid, url)

    @property
    def body(self):
        result = self._select(self._queries['article_body'])
        return result[0].text if len(result) else ''

    @property
    def title(self):
        result = self._select(self._queries['article_title'])
        return result[0].text if len(result) else ''

    @property
    def url(self):
        result = self._url
        return result if len(result) else ''
