# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 eTools (Web)
"""

from lxml import html
from urllib.parse import quote
from searx.utils import extract_text, eval_xpath

# about
about = {
    "website": 'https://www.etools.ch',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['general']
paging = False
safesearch = True

base_url = 'https://www.etools.ch'
search_path = '/searchAdvancedSubmit.do'\
    '?query={search_term}'\
    '&pageResults=20'\
    '&safeSearch={safesearch}'


def request(query, params):
    if params['safesearch']:
        safesearch = 'true'
    else:
        safesearch = 'false'

    params['url'] = base_url + search_path.format(search_term=quote(query),
                                                  safesearch=safesearch)

    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, '//table[@class="result"]//td[@class="record"]'):
        url = eval_xpath(result, './a/@href')[0]
        title = extract_text(eval_xpath(result, './a//text()'))
        content = extract_text(eval_xpath(result, './/div[@class="text"]//text()'))

        # ignore referal to other engine
        if "www.google.com/search?" in url:
            continue

         results.append({'url': url,
                        'title': title,
                        'content': content})

        # get total number of results
        for result in eval_xpath(dom, '//strong[5]'):

            number_of_results = extract_text(result, './text()').replace(',', '')

            results.append({'number_of_results': int(number_of_results)})

    return results
