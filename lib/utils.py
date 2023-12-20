import discord
import logging
import os
import shutil
from urllib.parse import urlparse
from yt_dlp import YoutubeDL

MUSIC_DIRNAME = "music"

YTDL_OPTS = {
  "quiet": True,
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

# create a discord.Embed object
def create_embed(message: str):
  embed = discord.Embed(description=message)
  return embed

# search query and return an info obj & a streamable url
def search(query):
  if is_valid_url(query):
    return download_stream_url(query)
  else:
    return download_yt_query(query)

def delete_temp_dir():
  temp_dir = os.path.join(os.getcwd(), MUSIC_DIRNAME)
  if os.path.isdir(temp_dir):
    shutil.rmtree(temp_dir)

# verifies whether the given URL is valid.
# returns True if valid, False if invalid.
def is_valid_url(url):
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except ValueError:
    return False

# downloads a YouTube/Soundcloud URL.
# returns a tuple on success, None otherwise.
def download_stream_url(url):
  result = None
  log.info(f"Downloading URL: \"{url}\"")
  with YoutubeDL(YTDL_OPTS) as ydl: 
    try:
      result = ydl.sanitize_info(ydl.extract_info(url, download=True))
    except Exception as e:
      log.error(e)
      return None

  title = result['title']
  webpage_url = result['webpage_url']
  filepath = result["requested_downloads"][0]["filepath"]

  return (title, webpage_url, filepath)

# downloads the first result from a YouTube search query
# returns a tuple on success, None otherwise.
def download_yt_query(query):
  result = None
  log.info(f"Downloading YouTube search query: \"{query}\"")
  with YoutubeDL(YTDL_OPTS) as ydl:
    try:
      result = ydl.sanitize_info(ydl.extract_info("ytsearch:{}".format(query), download=True))['entries'][0]
    except Exception as e:
      log.error(e)
      return None
  
  title = result['title']
  webpage_url = result['webpage_url']
  filepath = result["requested_downloads"][0]["filepath"]

  return (title, webpage_url, filepath)
