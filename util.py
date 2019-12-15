import config
import json
import requests
import time
import pandas as pd
import numpy as np

## this function calls the Google Books API, passing in search query, subject, 
## API key, and number of calls as the parameter. Each call returns 40 results
def google_books_call(query, subject, api_key, n_calls):
    data = []
    offset = 0
    while n_calls > 0:
        url = f'https://www.googleapis.com/books/v1/volumes?q={query}+subject:{subject}&projection=full&maxResults=40&startIndex={offset}&key={config.googlebooks_api_key}'
        response = requests.request('GET', url, allow_redirects=False)
        load = json.loads(response.text)
        print(load)
        offset += 40
        n_calls -= 1
        time.sleep(1)
        
        ## skips entries with no information
        try:
            data.append(load['items'])
        except KeyError:
            continue
    return data

def filter_keys(data, keys):
    return{key: data[key] if key in data.keys() else None for key in keys}

## parses books into a list of dictionaries
def parse_books(data, keys1, keys2):
    volumes = []
    for item in data:
        for book in item:
            volInfo = book['volumeInfo']
            voldict = filter_keys(keys=keys1, data=volInfo)
            if type(voldict['readingModes']) is dict:
                    voldict['readingModes'] = voldict['readingModes']['image']
            saleInfo = book['saleInfo']
            saledict = filter_keys(keys=keys2, data=saleInfo)
            if type(saledict['listPrice']) is dict:
                saledict['listPrice'] = saledict['listPrice']['amount']
            bigdict = {**voldict, **saledict}
            volumes.append(bigdict)
    return volumes

def handle_list(x):
    if type(x) == list:
        return ', '.join(x)
    else:
        return x

def clean_df(df):    
    df = df[~df.categories.isnull()]

    df['authors'] = df['authors'].apply(lambda x: handle_list(x))
    df['categories'] = df['categories'].apply(lambda x: handle_list(x))
    
    df['title'] = df['title'].str.replace('"', '')
    df['publisher'] = df['publisher'].str.replace('"', '')

    df.dropna(subset=['publishedDate'], inplace=True)
    df['publishedDate'] = df['publishedDate'].str.replace('*', '')
    
    df = df[(df['publishedDate'] != '1644') & (df['publishedDate'] != '1495') & 
            (df['publishedDate'] != '1552') & (df['publishedDate'] != '200?')]
    df['month'] = (pd.to_datetime(df['publishedDate'], utc=True).dt.month).astype(int)
    df['year'] = pd.to_datetime(df['publishedDate'], utc=True).dt.year

    df.rename(columns={"readingModes": "images"}, inplace=True)

    df = df[['title', 'subtitle', 'authors', 'publisher', 'month', 'year', 
             'categories', 'pageCount', 'listPrice', 'images', 'isEbook', 
             'ratingsCount', 'averageRating', 'description']]
    df = df[(df['ratingsCount'] >= 1) & (df['year'] >= 2009)]
    return df

