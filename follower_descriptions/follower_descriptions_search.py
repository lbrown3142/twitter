__author__ = 'LEWBROWN'

import oauth2
import time
import urllib.request
import json

def get_follower_ids(uni_handle):
    url1 = "https://api.twitter.com/1.1/followers/ids.json"
    params = {
    "oauth_version": "1.0",
    "oauth_nonce": oauth2.generate_nonce(),
    "oauth_timestamp": int(time.time())
    }

    consumer = oauth2.Consumer(key="Szer02dozR3wKB1vrHV3TydrF", secret="z1j9tjcZoUMEKUK5kOgf63fD351sJieMN6m40AsywDf6r5tB6h")
    token = oauth2.Token(key="3369108609-zxUHGjtfJ3Cw3lA75EJWkb089vReuXBiZXf7q53", secret="SwiKSbbCH0wBwFV1Xxe0Wl012gNl4Dk8I5M1l1CZLD2vN")
    params["oauth_consumer_key"] = consumer.key
    params["oauth_token"] = token.key

    '''
    consumer = oauth2.Consumer(key="nvoe6zVUm0TLGC6skoYSHrcMB", secret="LdwAMy9BPrp9iiWQOOGOYL6ityc0onX4nuQLIv4QIoNd6vL2jL")
    token = oauth2.Token(key="1722158881-RAtsr4yeUhBlvKvqGVSDx5fJcMh4H31GHZV4E17", secret="5JjwxAp8RhWOaGqjlwbnklRDBsKZzbYtqrmFEWhKKa3T7")
    params["oauth_consumer_key"] = consumer.key
    params["oauth_token"] = token.key
    '''

    params["screen_name"] = uni_handle


    cursor = -1
    num_attempts = 0
    results = []
    while cursor != 0:

        num_attempts += 1
        params["cursor"] = cursor

        req = oauth2.Request(method="GET", url=url1, parameters=params)
        signature_method = oauth2.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, consumer, token)
        url = req.to_url()
        response = urllib.request.urlopen(url)
        data = response.read().decode('utf-8')
        data = json.loads(data)

        cursor = data["next_cursor"]
        results = results + data["ids"]



        if num_attempts == 15:
            #print "ID limit reached, sleeping for 15 minutes"
            num_attempts = 0
            time.sleep(930)

        break;
        #print "data: " + str(len(data["ids"]))
        #print "results: " + str(len(results))
        #print num_attempts
        #time.sleep(3)

    #print "final result: " + str(len(results))
    return results





def id_splitter(batch_ids, n):
    return [batch_ids[i:i + n] for i in range(0, len(batch_ids), n)]




def get_followers_data(follower_ids):

    url1 = "https://api.twitter.com/1.1/users/lookup.json"
    params = {
    "oauth_version": "1.0",
    "oauth_nonce": oauth2.generate_nonce(),
    "oauth_timestamp": int(time.time())
    }

    '''
    consumer = oauth2.Consumer(key="nvoe6zVUm0TLGC6skoYSHrcMB", secret="LdwAMy9BPrp9iiWQOOGOYL6ityc0onX4nuQLIv4QIoNd6vL2jL")
    token = oauth2.Token(key="1722158881-RAtsr4yeUhBlvKvqGVSDx5fJcMh4H31GHZV4E17", secret="5JjwxAp8RhWOaGqjlwbnklRDBsKZzbYtqrmFEWhKKa3T7")
    params["oauth_consumer_key"] = consumer.key
    params["oauth_token"] = token.key
    '''

    consumer = oauth2.Consumer(key="Szer02dozR3wKB1vrHV3TydrF", secret="z1j9tjcZoUMEKUK5kOgf63fD351sJieMN6m40AsywDf6r5tB6h")
    token = oauth2.Token(key="3369108609-zxUHGjtfJ3Cw3lA75EJWkb089vReuXBiZXf7q53", secret="SwiKSbbCH0wBwFV1Xxe0Wl012gNl4Dk8I5M1l1CZLD2vN")
    params["oauth_consumer_key"] = consumer.key
    params["oauth_token"] = token.key


    params["user_id"] = str(follower_ids)[:-1][1:]


    req = oauth2.Request(method="GET", url=url1, parameters=params)        #changed from "GET" to "POST" as twitter recommends
    signature_method = oauth2.SignatureMethod_HMAC_SHA1()
    req.sign_request(signature_method, consumer, token)
    url = req.to_url()

    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    data = json.loads(data)

    return data





def search_distribute(json_list, uni_handle, query):
    results = []

    for people in json_list:
        description = (people["description"].encode("utf-8", errors="ignore")).lower()

        for search_term in query:
            try:
                search_term_bytes = search_term.encode('utf-8')
                if search_term_bytes in description:
                    results.append({"user_id": people["id_str"], "screen_name": people["screen_name"], "followed_uni_handle": uni_handle, "category": search_term, "user_description": people["description"], "url": 'https://twitter.com/' + people['screen_name']})
            except TypeError:
                throw

    return results

def DoSearch(uni_handle, search_terms):
    count = 0
    results = []

    user_ids = get_follower_ids(uni_handle)
    split_ids = id_splitter(user_ids, 100)
    for people in split_ids:
        count += 1
        if count == 30:
            count = 0
            # print" search limit reached, sleeping for 15 minutes"
            # time.sleep(930)
            return results

        followers_data = get_followers_data(people)
        result = search_distribute(followers_data, uni_handle, search_terms)
        if result:
            results.append(result)

    return results



