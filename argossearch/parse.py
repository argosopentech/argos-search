from urllib import request
import bs4
from bs4 import BeautifulSoup, NavigableString

def get_text(bs):
    if isinstance(bs, bs4.element.NavigableString):
        return str(bs)
    return "\n".join([get_text(content) for content in bs.contents])

def network_get(url):
    req = request.Request(url)
    response = request.urlopen(req)
    return response.read().decode()

class Link:
    def __init__(self, bs):
        self.bs = bs
        self.text = get_text(bs)
        self.url = self.bs['href']

    def __str__(self):
        return f'[{self.text}]({self.url})'

class Page:
    def __init__(self, url):
        self.url = url
        self.raw_text = network_get(self.url)
        self.soup = BeautifulSoup(self.raw_text, features="html.parser")
        self.text = get_text(self.soup)
        self.links = [Link(link) for link in self.soup.find_all('a')]


def crawl_domain(url, depth=2):
    if depth < 0: return list()
    print('crawl_domain', f'url={url}', f'depth={depth}')
    page = Page(url)
    to_return = [page]
    if len(page.links) > 0:
        for link in page.links:
            try:
                crawl = crawl_domain(link.url, depth - 1)
                to_return += crawl
            except:
                pass
    return to_return

crawl = crawl_domain('https://www.argosopentech.com')
