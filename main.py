# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 11:32:07 2023

@author: Arush
"""

import dotenv
import os
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from termcolor import cprint
import pandas as pd
from datetime import datetime 
from langdetect import detect
from cleantext import clean
from nltk.sentiment import SentimentIntensityAnalyzer

def main():

    # API Information
    api_service_name = 'youtube'
    api_service_version = 'v3'
    dotenv.load_dotenv()
    api_key = os.getenv('API_KEY')
    
    # Build Service
    youtube = build(api_service_name, api_service_version, developerKey=api_key)
    
    #Get Video ID
    videoId = getVideoId()

    # Get Comments
    comments = getComments(youtube, videoId)
    df = pd.DataFrame(comments)    
    
    # Vader Sentiment Analysis
    df = vader(df)
    
    # Create CSV
    cprint('creating CSV', 'cyan')
    dtstr = datetime.now().strftime("%y%m%d%H%M%S")
    df.to_csv(f'./data/{dtstr}.csv', index=False)  
        
        

def getVideoId():
    cprint("COMMENTS RETRIEVAL", 'magenta', attrs=['bold'])
    while True:
        url = input("Enter YouTube link: ")
        url_data = urlparse(url)
        if url_data.hostname == 'youtu.be':
            return url_data.path[1:]
        if url_data.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com', 'music.youtube.com']:
            path = url_data.path
            if path == '/watch':
                return parse_qs(url_data.query)['v'][0]
            if path.startswith('/watch/'):
                return path.split('/')[1]
            if path.startswith('/embed/'):
                return path.split('/')[2]
            if path.startswith('/v/'):
                return path.split('/')[2]
        cprint("Invalid URL! Try Again.", "red", attrs=["bold"])

def getComments(service, videoId):
    request = service.commentThreads().list(
        part='snippet',
        videoId=videoId,
        order='time',
        textFormat="plainText"
    )
    
    commentIds, comments, likeCounts = [], [], []
    
    while True:
        cprint('retrieving data...', 'cyan')
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']
            text = comment['snippet']['textOriginal']
            try:
                # Check if the comment is in english
                if text and detect(text) == 'en':\
                    # Append Comment text without emojis
                    comments.append(clean(text, no_emoji=True))
                    commentIds.append(comment['id'])
                    likeCounts.append(comment['snippet']['likeCount'])
            except:
                continue
        #if 'nextPageToken' in response and len(comments) < 2000:
        #    request = service.commentThreads().list(
        #        part='snippet',
        #        videoId=videoId,
        #        order='time',
        #        textFormat="plainText",
        #        pageToken=response['nextPageToken']
        #    )
        #else:
        return dict({'ID': commentIds, 'text': comments, 'Likes': likeCounts})
    
# VADER MODEL ANALYSIS
def vader(data):
    result = {}
    sia = SentimentIntensityAnalyzer()
    for i, row in data.iterrows():
        scores = sia.polarity_scores(row['text'])
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound > -0.05:
            sentiment = 'neutral'
        else:
            sentiment = 'negative'
        scores['sentiment'] = sentiment
        result[row['ID']] = scores
    df = pd.DataFrame(result).T.reset_index().rename(columns={'index': 'ID'})
    return data.merge(df, how='left', on=['ID'])


main()