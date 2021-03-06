__author__ = 'LEWBROWN'

import oauth2
import time
import urllib.request
import json

#consumer = oauth2.Consumer(key="nvoe6zVUm0TLGC6skoYSHrcMB", secret="LdwAMy9BPrp9iiWQOOGOYL6ityc0onX4nuQLIv4QIoNd6vL2jL")
#token = oauth2.Token(key="1722158881-RAtsr4yeUhBlvKvqGVSDx5fJcMh4H31GHZV4E17", secret="5JjwxAp8RhWOaGqjlwbnklRDBsKZzbYtqrmFEWhKKa3T7")

#consumer = oauth2.Consumer(key="Szer02dozR3wKB1vrHV3TydrF", secret="z1j9tjcZoUMEKUK5kOgf63fD351sJieMN6m40AsywDf6r5tB6h")
#token = oauth2.Token(key="3369108609-zxUHGjtfJ3Cw3lA75EJWkb089vReuXBiZXf7q53", secret="SwiKSbbCH0wBwFV1Xxe0Wl012gNl4Dk8I5M1l1CZLD2vN")

# Steve's access tokens
consumer = oauth2.Consumer(key="zxz7NFdedpCNfq8SebFXEBs0X", secret="9snozBZGrBxmtzR8rwMybwnfHxkfxPcEmiLvRg6LcxusOvWkZV")
token = oauth2.Token(key="21507127-pm8sxHNxv4LhIkoAnLAwPLc1vMQLWdsv2POmV2w3l", secret="Q8d6twxYHbeHIjut0p1fNTMdVP5P0WTjaYDcI1SljSBrX")


def get_users_by_screen_name(screen_names):   #18k per 15 mins

    url1 = "https://api.twitter.com/1.1/users/lookup.json"
    params = {
    "oauth_version": "1.0",
    "oauth_nonce": oauth2.generate_nonce(),
    "oauth_timestamp": int(time.time())
    }

    params["oauth_consumer_key"] = consumer.key
    params["oauth_token"] = token.key

    # Convert list to csv
    screen_names = ','.join(screen_names)
    params["screen_name"] = screen_names

    req = oauth2.Request(method="GET", url=url1, parameters=params)        #changed from "GET" to "POST" as twitter recommends
    signature_method = oauth2.SignatureMethod_HMAC_SHA1()
    req.sign_request(signature_method, consumer, token)
    url = req.to_url()

    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    data = json.loads(data)

    return data

def get_follower_ids(uni_handle, cursor):           #75k per 15 mins

    url1 = "https://api.twitter.com/1.1/followers/ids.json"
    params = {
    "oauth_version": "1.0",
    "oauth_nonce": oauth2.generate_nonce(),
    "oauth_timestamp": int(time.time())
    }

    params["oauth_consumer_key"] = consumer.key
    params["oauth_token"] = token.key
    params["screen_name"] = uni_handle


    num_attempts = 0
    results = []


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



    #if num_attempts == 15:
        #print "ID limit reached, sleeping for 15 minutes"
        #num_attempts = 0
        #time.sleep(930)

        #need to upload first batch and start a new task for second batch so it uploads results in real time instead of waiting



    #    break
        #print "data: " + str(len(data["ids"]))
        #print "results: " + str(len(results))
        #print num_attempts
        #time.sleep(3)

    #print "final result: " + str(len(results))
    return results, cursor






def get_followers_data(follower_ids):   #18k per 15 mins

    url1 = "https://api.twitter.com/1.1/users/lookup.json"
    params = {
    "oauth_version": "1.0",
    "oauth_nonce": oauth2.generate_nonce(),
    "oauth_timestamp": int(time.time())
    }

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
        if len(people["description"]) < 6:
            continue

        description = (people["description"].encode("utf-8", errors="ignore")).lower()

        for search_term in query:

            search_term_bytes = search_term.encode('utf-8')
            if search_term_bytes in description:
                results.append({"user_id": people["id_str"], "screen_name": people["screen_name"], "location": people["location"], "followed_uni_handle": uni_handle, "category": search_term, "user_description": people["description"], "url": 'https://twitter.com/' + people['screen_name']})


    return results


# Get profile info - not currently working
def get_profile_banner_info(screen_name, user_id):
    # e.g.
    # https://api.twitter.com/1.1/users/profile_banner.json?screen_name=rjsinha

    url1 = "https://api.twitter.com/1.1/users/profile_banner.json"
    params = {
        "oauth_version": "1.0",
        "oauth_nonce": oauth2.generate_nonce(),
        "oauth_timestamp": int(time.time())
    }

    params["oauth_consumer_key"] = consumer.key
    params["oauth_token"] = token.key
    #params["screen_name"] = screen_name
    params["user_id"] = user_id

    req = oauth2.Request(method="GET", url=url1,
                         parameters=params)
    signature_method = oauth2.SignatureMethod_HMAC_SHA1()
    req.sign_request(signature_method, consumer, token)
    url = req.to_url()

    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    data = json.loads(data)

    return data

