import os
import dotenv
import logging
import pytz
import requests
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# project imports
from commands.music import search

# environment variables
dotenv.load_dotenv()
server_id = os.getenv('SERVER_ID')
text_channel_id = os.getenv('TEXT_CHANNEL_ID')
voice_channel_id = os.getenv('VOICE_CHANNEL_ID')
giphy_key = os.getenv('GIPHY_KEY')

# set up logging
log = logging.getLogger('bot')

class friday(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.FFMPEG_OPTIONS = {
      'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
      'options': '-vn'
    }
  
  def _getGif(self):
    try:
      r = requests.get('http://api.giphy.com/v1/gifs/search', params = {
        'q': 'Friday',
        'api_key': giphy_key,
        'limit': '1',
        'offset': '0',
        'rating': 'pg-13',
        'lang': 'en'
      })
      url = r.json()['data'][0]['url']
      return url
    except Exception as e:
      log.error(e)
      return None

  async def _join(self):
    try:
      guild = self.bot.get_guild(int(server_id))
      voice_channel = self.bot.get_channel(int(voice_channel_id))
      if voice_channel is None or guild is None:
        log.warning('voice/guild was not found')
        return False

      voice_client = None
      for voice in self.bot.voice_clients:
        if voice.guild == guild:
          voice_client = voice
      
      if voice_client is None: # if bot is not in a voice channel then connect to author's voice channel
        await voice_channel.connect()
      elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)
      return True
    except Exception as e:
      log.error(e)
    return False

  async def _play_friday(self):
    info, source = search('https://www.youtube.com/watch?v=kfVsfOSbJY0')
    try:
      guild = self.bot.get_guild(int(server_id))
      text_channel = self.bot.get_channel(int(text_channel_id))
      if await self._join() is False: # if bot failed to join then exit
        log.error('Failed to join the target voice channel...')
        return
      voice_client = None
      for voice in self.bot.voice_clients:
        if voice.guild == guild:
          voice_client = voice
      if voice_client.is_playing():
        voice_client.stop()
      gif_url = self._getGif()
      voice_client.play(await discord.FFmpegOpusAudio.from_probe(source, **self.FFMPEG_OPTIONS))
      await text_channel.send('TGIF!! Here is \"{}\" to celebrate this amazing Friday! {}'.format(info['title'], gif_url))
      log.info('Successfully started playing Friday ;)')
    except Exception as e:
      log.error(e)

  @commands.Cog.listener()
  async def on_ready(self):
    bot = self.bot
    for guild in bot.guilds:
      log.info('{} has joined {}'.format(bot.user.name, guild.name))
    try:
      # schedule task
      self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('US/Pacific'))
      self.scheduler.start()
      self.scheduler.add_job(self._play_friday, trigger='cron', day='*', hour='20', minute='0', day_of_week='fri')
    except Exception as e:
      log.error(e)

def setup(bot):
  try:
    bot.add_cog(friday(bot))
    log.info('Successfully set up friday')
  except Exception as e:
    log.info('Error occured when setting up friday\n')
    log.error(e)