from urllib import request
import bs4
from bs4 import BeautifulSoup, NavigableString

def get_text(bs):
    if isinstance(bs, bs4.element.NavigableString):
        return str(bs)
    return "\n".join([get_text(content) for content in bs.contents])

def get(url):
    req = request.Request(url)
    response = request.urlopen(req)
    response_str = response.read().decode()
    soup = BeautifulSoup(response_str, features="html.parser")
    return get_text(soup)

class Page:
    def __init__(self, url):
        self.url = url
        self.text = get(url)

print(get("https://www.argosopentech.com"))
