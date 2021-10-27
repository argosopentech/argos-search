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

class URL:
    def __init__(self, url):
        self.url = url
        if not self.validate(): raise Exception()

    def validate(self):
        colon_index = self.url.find(':')
        if colon_index < 0:
            return False
        self.protocal = self.url[0:colon_index]
        domain_start = self.url.find('//')
        if domain_start < 0:
            return False
        domain_start += 2
        domain_end = self.url.find('/', domain_start)
        if domain_end < 0:
            domain_end = len(self.url)
        self.domain = self.url[domain_start:domain_end] 
        return True

    def __str__(self):
        return self.url

class Page:
    def __init__(self, url):
        self.url = url
        self.raw_text = network_get(self.url)
        self.soup = BeautifulSoup(self.raw_text, features="html.parser")
        self.text = get_text(self.soup)
        self.links = list()
        for a in self.soup.find_all('a'):
            try:
                url = URL(a['href'])
                self.links.append(url)
            except:
                pass


pages = dict()
            
def crawl(url, depth=2, jump_domains=False):
    print('crawl_domain', f'url={url}', f'depth={depth}', f'jump_domains={jump_domains}')
    if depth < 0: return list()
    if str(url) in pages.values(): return list()
    page = Page(url)
    pages[str(url)] = page
    to_return = [page]
    for link in page.links:
        try:
            if (not jump_domains) and link.domain != page.url.domain:
                continue
            print(link)
            to_return += crawl(link, depth - 1, jump_domains)
        except:
            pass
    return to_return


argosopentech = URL('https://www.argosopentech.com')
ltcommunity = URL('https://community.libretranslate.com')
crawl = crawl(argosopentech, 2, True)
print(crawl)


