# customized version of https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34#file-music-py
import asyncio
import discord
import logging
from async_timeout import timeout
from functools import partial

# project imports
from lib.utils import create_embed
from lib.utils import delete_temp_dir
from lib.utils import search
from lib.utils import FFMPEG_OPTS

# set up logging
log = logging.getLogger('bot')

class YTDLSource():

  def __init__(self, source, title, webpage_url, filepath, requester):
    self.source = source
    self.requester = requester

    self.title = title
    self.web_url = webpage_url
    self.filepath = filepath

  @classmethod
  async def create(cls, ctx, query: str, loop):
    loop = loop or asyncio.get_event_loop()
    to_run = partial(search, query=query)
    id = ''

    try:
      id = ctx.author.id
    except Exception as e:
      if isinstance(e, AttributeError) is False:
        log.error(e)

    title, webpage_url, filepath = await loop.run_in_executor(None, to_run)

    if ctx.voice_client and ctx.voice_client.is_playing():
      await ctx.send(embed=create_embed('**Queued up** \"{}\"'.format(title)))
    
    source = await discord.FFmpegOpusAudio.from_probe(filepath, **FFMPEG_OPTS, method='fallback')
    return cls(source, title=title, webpage_url=webpage_url, filepath=filepath, requester=id)

class MusicPlayer:

  __slots__ = ('bot', 'guild', 'channel', 'cog', 'queue', 'next', 'current', 'message')

  def __init__(self, ctx):
    self.bot = ctx.bot
    self.guild = ctx.guild
    self.channel = ctx.channel
    self.cog = ctx.cog

    self.queue = asyncio.Queue()
    self.next = asyncio.Event()

    self.message = None # now playing message
    self.current = None # current YTDLSource

    self.bot.loop.create_task(self.player_loop())
  
  def __after(self, e):
    if e:
      log.error(e)
    self.bot.loop.call_soon_threadsafe(self.next.set)

  def clear_queue(self):
    for _ in range(self.queue.qsize()):
      self.queue.get_nowait()
      self.queue.task_done()

    try:
      if self.current:
        self.next.clear()
        self.current.source.cleanup()
        self.current = None
    except Exception as e:
      log.error(e)

  def get_current(self):
    return self.current

  async def player_loop(self):
    if self.bot.is_closed():
      print("bot is closed!")
    while not self.bot.is_closed():
      self.next.clear()

      try:  # Wait for the next song. If we timeout cancel the player and disconnect
        async with timeout(60): # 60 seconds before timing out
          ytdlSource = await self.queue.get()
      except asyncio.TimeoutError:
        log.info('Queue seems to be empty. Cleaning up music player')
        return self.destroy(self.guild)
      
      self.current = ytdlSource

      try:
        self.guild.voice_client.play(ytdlSource.source, after=self.__after)
        if ytdlSource.requester != '':
          self.message = await self.channel.send(embed=create_embed('**Now Playing:**\n\"{}\"\nrequested by <@{}>'.format(ytdlSource.title, ytdlSource.requester)))

        await self.next.wait()

        # cleanup audio source
        ytdlSource.source.cleanup()

        self.current = None
      except Exception as e:
        log.error(e)
  
  def destroy(self, guild):
    try:
      delete_temp_dir()
    except Exception as e:
      log.error(e)

    # Disconnect and cleanup music player
    return self.bot.loop.create_task(self.cog.cleanup(guild))

