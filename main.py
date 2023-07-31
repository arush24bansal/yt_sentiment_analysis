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
    
    # Create CSV
    cprint('creating CSV', 'cyan')
    df = pd.DataFrame(comments)
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
            commentIds.append(comment['id'])
            comments.append(comment['snippet']['textOriginal'])
            likeCounts.append(comment['snippet']['likeCount'])
        if 'nextPageToken' in response and len(comments) < 2000:
            request = service.commentThreads().list(
                part='snippet',
                videoId=videoId,
                order='time',
                textFormat="plainText",
                pageToken=response['nextPageToken']
            )
        else:
            return dict({'ID': commentIds, 'text': comments, 'Likes': likeCounts})
        
main()