import os
import dotenv
import logging
import pytz
import requests
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# project imports
from commands.music_player import YTDLSource

# environment variables
dotenv.load_dotenv()
server_id = os.getenv('SERVER_ID')
text_channel_id = os.getenv('TEXT_CHANNEL_ID')
voice_channel_id = os.getenv('VOICE_CHANNEL_ID')
giphy_key = os.getenv('GIPHY_KEY')

# set up logging
log = logging.getLogger('bot')

class Friday(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.FFMPEG_OPTIONS = {
      'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
      'options': '-vn'
    }
  
  @classmethod
  def __getGif(cls):
    try:
      r = requests.get('http://api.giphy.com/v1/gifs/search', params = {
        'q': 'Friday',
        'api_key': giphy_key,
        'limit': '1',
        'offset': '0',
        'rating': 'pg-13',
        'lang': 'en'
      })
      return r.json()['data'][0]['url'] # return url
    except Exception as e:
      log.error(e)
      return ''

  async def __connect(self):
    try:
      guild = self.bot.get_guild(int(server_id))
      channel = self.bot.get_channel(int(voice_channel_id))
    
      vc = None
      for voice_client in self.bot.voice_clients:
        if voice_client.guild == guild:
          vc = voice_client
    
      if vc is None:  # if bot is not in a voice channel then simply connect to the target channel
        await channel.connect()
      elif vc.channel != channel: # bot is already in a channel so move it to the target channel
        await vc.move_to(channel)
      # if none are true then the bot is already in the target channel
      return True

    except Exception as e:
      log.error(e)
      return False

  async def __play_friday(self):
    try:
      guild = self.bot.get_guild(int(server_id))
      text_channel = self.bot.get_channel(int(text_channel_id))
      music = self.bot.get_cog('Music')
      music_player = None
      vc = None

      for voice_client in self.bot.voice_clients:
        if voice_client.guild == guild:
          vc = voice_client

      if vc is None:
        return

      if music.music_player_exists(guild=guild): # clear queue if music player already exists
        music_player = music.get_music_player(guild=guild)
        music_player.clear_queue()
        
      # create new music player
      music_player = music.get_music_player(guild=guild)

      class Object(): # create ctx to pass through YTDLSource.create()
        pass
      ctx = Object()
      ctx.voice_client = vc
      ctx.send = text_channel.send

      if await self.__connect() is False: # reconnect but if bot failed to join then exit
        log.error('Failed to join the target voice channel...')
        return

      gif_url = self.__getGif()
      ytdlSource = await YTDLSource.create(ctx, 'https://www.youtube.com/watch?v=kfVsfOSbJY0', loop=self.bot.loop)
      await text_channel.send('TGIF!! Here is \"{}\" to celebrate this amazing Friday!\n{}'.format(ytdlSource.title, gif_url))
      await music_player.queue.put(ytdlSource)
      log.info('Successfully started playing Friday ;)')

    except Exception as e:
      log.error(e)

  @commands.Cog.listener()
  async def on_ready(self):
    bot = self.bot
    for guild in bot.guilds:
      log.info('{} has joined {}'.format(bot.user.name, guild.name))
    try:
      # schedule task, every friday at 8:00pm PST
      self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('US/Pacific'))
      self.scheduler.start()
      self.scheduler.add_job(self.__play_friday, trigger='cron', day='*', hour='20', minute='0', day_of_week='fri')
    except Exception as e:
      log.error(e)

def setup(bot):
  try:
    bot.add_cog(Friday(bot))
    log.info('Successfully set up friday')
  except Exception as e:
    log.info('Error occured when setting up friday\n')
    log.error(e)