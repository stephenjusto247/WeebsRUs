import discord
import logging
import os
import requests
import shutil
import time
from yt_dlp import YoutubeDL, utils
from sclib import SoundcloudAPI, Track

MUSIC_DIRNAME = "music"
MAX_ATTEMPTS = 11

YTDL_OPTS = {
  "format": "bestaudio",
  "paths": {"home": "./{}/".format(MUSIC_DIRNAME)},
  'noplaylist': True,
  'force-ipv4': True,
}

FFMPEG_OPTS = {
  "before_options": "-nostdin", 
  'options': '-vn'
}

log = logging.getLogger('bot')

def create_embed(message: str): # create a discord.Embed object
  embed = discord.Embed(description=message)
  return embed

# search query and return an info obj & a streamable url
def search(query):
  try:
    api = SoundcloudAPI()  
    track = api.resolve(query)
    assert type(track) is Track
    url = track.get_stream_url()
    return (track.title, query, url)
  except:
    with YoutubeDL(YTDL_OPTS) as ydl:
      try: requests.get(query)
      except:
        for attempt in range(MAX_ATTEMPTS):
          log.info(f"Attempting to download ytsearch \"{query}\" ATTEMPT #{attempt + 1}")
          try:
            info = ydl.sanitize_info(ydl.extract_info("ytsearch:{}".format(query), download=True))['entries'][0]
            break
          except utils.DownloadError:
            time.sleep(attempt * 100 / 1000)
            continue   
      else:
        for attempt in range(MAX_ATTEMPTS):
          log.info(f"Attempting to download \"{query}\" ATTEMPT #{attempt + 1}")
          try:
            info = ydl.sanitize_info(ydl.extract_info(query, download=True))
            break
          except utils.DownloadError:
            time.sleep(attempt * 100 / 1000)
            continue   
    if 'entries' in info:
      info = info['entries'][0]
    title = info['title']
    webpage_url = info['webpage_url']
    filepath = info["requested_downloads"][0]["filepath"]
    return (title, webpage_url, filepath)

def delete_temp_dir():
  temp_dir = os.path.join(os.getcwd(), MUSIC_DIRNAME)
  if os.path.isdir(temp_dir):
    shutil.rmtree(temp_dir)
