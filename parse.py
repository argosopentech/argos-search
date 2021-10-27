import csv
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
    try:
        page = Page(url)
    except:
        return list()
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


whitelist = list()
with open('/home/videodesktop/git/argos-search/whitelists.csv') as whitelist_file:
    reader = csv.reader(whitelist_file)
    for row in reader:
        whitelist += row

white_data = list()
for domain in whitelist:
    url = URL(domain)
    print(f'Crawling {domain}')
    white_data += [page.text for page in crawl(url, 1, True)]

white_data = "\n".join(white_data)

white_lines = list()
for i in range(10, len(white_data), 10):
    white_lines.append(white_data[i-10:i])

blacklist = list()
with open('/home/videodesktop/git/argos-search/blacklist.csv') as blacklist_file:
    reader = csv.reader(blacklist_file)
    for row in reader:
        blacklist += row

black_data = list()
for domain in blacklist:
    url = URL(domain)
    print(f'Crawling {domain}')
    black_data += [page.text for page in crawl(url, 1, True)]

black_data = "\n".join(black_data)

black_lines = list()
for i in range(10, len(black_data), 10):
    black_lines.append(black_data[i-10:i])

with open('source', 'w') as src:
    with open('target', 'w') as tgt:
        for white_line in white_lines:
            if len(white_line.strip()) < 1: continue
            src.write(white_line + '\n')
            tgt.write('1\n')
        for black_line in black_lines:
            if len(black_line.strip()) < 1: continue
            src.write(black_line + '\n')
            tgt.write('0\n')



    

