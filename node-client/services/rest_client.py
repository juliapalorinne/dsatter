import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import requests
from typing import Union
from util.helpers import catch_exception_sleep

class RESTClient:

    @staticmethod
    @catch_exception_sleep(5)
    def get(url: str) -> Union[dict, None]:
        res = requests.get(url)
        return None if res.status_code != 200 else res.json()


    @staticmethod
    def post(data: dict, url: str) -> dict:
        res = requests.post(url, json=data)
        return res.json()


if __name__ == '__main__':
    data_post = {
        "name": "morpheus",
        "job": "leader"
    }

    expected_get = {
        "data": {
            "id": 2,
            "email": "janet.weaver@reqres.in",
            "first_name": "Janet",
            "last_name": "Weaver",
            "avatar": "https://reqres.in/img/faces/2-image.jpg"
        },
        "support": {
            "url": "https://reqres.in/#support-heading",
            "text": "To keep ReqRes free, contributions towards server costs are appreciated!"
        }
    }

    res_get  = RESTClient.get('https://reqres.in/api/users/2')
    res_post = RESTClient.post(data_post, 'https://reqres.in/api/users')

    def check_post_response(post_data, post_response) -> bool:
        #return {**a, **{ "id", "createdAt"}}
        if not {"id", "createdAt", *post_data.keys()} == set(post_response):
            # Key missing from response
            return False
        if not post_data.items() <= post_response.items():
            # Returned value differs from posted
            return False

        # Check rest of the expected return fields
        return post_response['id']        is not None and len(post_response['id']) > 0 and \
               post_response['createdAt'] is not None and len(post_response['createdAt']) > 0

    if expected_get == res_get:
        print('GET returns correct value')
    else:
        print('GET return wrong value:', res_get)

    if check_post_response(data_post, res_post):
        print('POST return correct value')
    else:
        print('POST returns wrong value:', res_post)
