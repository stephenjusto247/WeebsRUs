import requests
import discord
from youtube_dl import YoutubeDL

YTDL_OPTS = {
  'format': 'bestaudio/best',
  'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
  'restrictfilenames': True,
  'noplaylist': True,
  'nocheckcertificate': True,
  'ignoreerrors': False,
  'logtostderr': False,
  'quiet': False,
  'no_warnings': True,
  'default_search': 'auto',
  'source_address': '0.0.0.0'
}

FFMPEG_OPTS = {
  'before_options': '-nostdin', 
  'options': '-vn'
}

def create_embed(message: str): # create a discord.Embed object
  embed = discord.Embed(description=message)
  return embed

def search(query):  # search query and return an info obj & a streamable url
  with YoutubeDL(YTDL_OPTS) as ydl:
    try: requests.get(query)
    except: info = ydl.extract_info("ytsearch:{}".format(query), download=True)['entries'][0]
    else: info = ydl.extract_info(query, download=True)
  return (info, info['formats'][0]['url'])