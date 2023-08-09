# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Discourse Forums

"""

from urllib.parse import urlencode
from dateutil import parser
import html

from searx.exceptions import SearxEngineException

about = {
    "website": "https://discourse.org/",
    "wikidata_id": "Q15054354",
    "official_api_documentation": "https://docs.discourse.org/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

base_url = None
search_endpoint = '/search.json?'

# ['latest', 'likes', 'views', 'latest_topic']
api_order = 'likes'
paging = True


def request(query, params):
    """ https://docs.discourse.org/#tag/Search/operation/search """
    if len(query) <= 2:
        raise SearxEngineException('For engines using discourse the length of the search query must be at least 3 chars!')

    args = urlencode({
            'q': query + f' order:{api_order}',
            'page': params['pageno'],
        })

    params['url'] = base_url + search_endpoint + args
    params['headers'].update({
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
    })

    return params


def response(resp):

    results = []
    json_data = resp.json()

    if ('topics' or 'posts') not in json_data.keys():
        return []

    for post, result in zip(json_data['posts'], json_data['topics']):

        status = " | Closed" if result.get('closed', '') else " | Open"
        comments = result.get('posts_count', 1)

        url = f"{base_url}/t/{result['id']}"
        publishedDate = parser.parse(result['created_at'])

        content = '@' + post.get('username', '')

        if int(comments) > 1:
            content += f' | Comments: {comments}'

        if result.get('has_accepted_answer', ''):
            content += ' | Answered'
        else:
          if int(comments) > 1:
              content += ' | No Accepted Answer'

        results.append(
            {
                'url': url,
                'title': html.unescape(str(result['title']) + status),
                'content': html.unescape(content),
                'publishedDate': publishedDate,
                'upstream': {'topics': result},
            }
        )

    results.append({'number_of_results': len(json_data['topics'])})

    return results

