import json
import shelve
import urllib.parse
from io import BytesIO

import requests
from PIL import Image

import colorgram
from colorsnap import snap_color


def europeana_generator(query, eu_key):
    cursor = '*'
    has_more = True

    while has_more:
        response = requests.get('https://www.europeana.eu/api/v2/search.json?wskey={}&query={}&media=true&reusability=open&rows=100&cursor={}'.format(eu_key, query, cursor))
        data = response.json()

        for item in data['items']:
            yield item

        if 'nextCursor' in data:
            cursor = urllib.parse.quote_plus(data['nextCursor'])
        else:
            has_more = False

#
# START
#

cache = shelve.open('credentials_cache')

if 'europeana_public_key' in cache:
    eu_key = cache['europeana_public_key']
else:
    print('What\'s your Europeana API key?')
    eu_key = input()
    cache['europeana_public_key'] = eu_key

print('This might take a while...')

final_items = list()
for item in europeana_generator('woodcuts AND japan', eu_key):
    processed_item = dict()

    if not 'edmIsShownAt' in item:
        continue

    processed_item['url'] = item['edmIsShownAt'][0]
    processed_item['rights'] = item['rights'][0]
    processed_item['title'] = item['title'][0]
    processed_item['provider'] = item['dataProvider'][0]
    processed_item['image'] = item['edmPreview'][0]
    processed_item['colors'] = list()
    processed_item['labels'] = list('hej')

    # color extraction
    response = requests.get(item['edmPreview'][0])
    img = Image.open(BytesIO(response.content))
    colors = colorgram.extract(img, 5)
    for color in colors:
        processed_item['colors'].append('#%02x%02x%02x' % color.rgb)

    final_items.append(processed_item)

with open('data.json', 'w') as outfile:
    json.dump(final_items, outfile)
