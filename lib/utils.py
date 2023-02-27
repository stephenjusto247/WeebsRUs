import requests
import discord
from yt_dlp import YoutubeDL

YTDL_OPTS = {
  'noplaylist': True
}

FFMPEG_OPTS = {
  "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
  'options': '-vn'
}

def create_embed(message: str): # create a discord.Embed object
  embed = discord.Embed(description=message)
  return embed

def extract_audio_url(info):
  if info is not None:
    for requested_format in info['requested_formats']:
      # when "fps" is None, the format is audio only
      if requested_format['fps'] is None:
        return requested_format['url']
  return ''

# search query and return an info obj & a streamable url
def search(query):  
  with YoutubeDL(YTDL_OPTS) as ydl:
    try: requests.get(query)
    except: info = ydl.sanitize_info(ydl.extract_info("ytsearch:{}".format(query), download=False))['entries'][0]
    else: info = ydl.sanitize_info(ydl.extract_info(query, download=False))
  return (info, extract_audio_url(info))