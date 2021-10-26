import bs4
from bs4 import BeautifulSoup, NavigableString

def get_text(bs):
    if isinstance(bs, bs4.element.NavigableString):
        return str(bs)
    return "\n".join([get_text(content) for content in bs.contents])


with open("index.html") as fp:
    soup = BeautifulSoup(fp, features="html.parser")
    print(get_text(soup))
