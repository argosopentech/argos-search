import json
import csv
from urllib import request
import bs4
from bs4 import BeautifulSoup, NavigableString

def network_get(url):
    req = request.Request(url)
    response = request.urlopen(req)
    return response.read().decode()

def get_text(bs):
    if isinstance(bs, bs4.element.NavigableString):
        return str(bs)
    return " ".join([get_text(content) for content in bs.contents])

class Page:
    def __init__(self, url):
        self.url = url
        raw_text = network_get(self.url)
        soup = BeautifulSoup(raw_text, features="html.parser")
        self.links = [str(link['href']) for link in soup.find_all('a')]
        text = get_text(soup)

    def value(self):
        return json.dumps({'url': self.url, 'links': self.links})

    def __str__(self):
        return f'Page: {self.url}'

    def __repr__(self):
        return str(self)


pages = dict()
            
def crawl(url, depth=1, jump_domains=True):
    print('crawl_domain', f'url={url}', f'depth={depth}', f'jump_domains={jump_domains}')
    if str(url) in pages.values(): return list()
    try:
        page = Page(url)
    except:
        return list()
    pages[str(url)] = page
    to_return = [page]
    if depth > 0:
        for link in page.links:
            try:
                if (not jump_domains) and link.domain != page.url.domain:
                    continue
                to_return += crawl(link, depth - 1, jump_domains)
            except:
                pass
    return to_return

whitelist = list()
with open('whitelists.csv') as whitelist_file:
    reader = csv.reader(whitelist_file)
    for row in reader:
        whitelist += row

for whitelisted in whitelist:
    crawl(whitelisted)

pages_object = dict()
for url, page in pages.items():
    pages_object[url] = page.value()

pages_json = json.dumps(pages_object)

print(pages_json)
