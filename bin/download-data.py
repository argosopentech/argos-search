

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



    