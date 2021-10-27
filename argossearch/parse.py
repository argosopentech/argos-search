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

class Page:
    def __init__(self, url):
        self.url = url
        self.raw_text = network_get(self.url)
        self.soup = BeautifulSoup(self.raw_text, features="html.parser")
        self.text = get_text(self.soup)
        print(self.text)


page = Page("https://www.argosopentech.com")
