# customized version of https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34#file-music-py
import discord
import logging
import asyncio
from async_timeout import timeout
from functools import partial

# project imports
from lib.utils import create_embed
from lib.utils import search
from lib.utils import FFMPEG_OPTS

# set up logging
log = logging.getLogger('bot')

class YTDLSource():

  def __init__(self, source, data, requester):
    self.source = source
    self.requester = requester

    self.title = data.get('title')
    self.web_url = data.get('webpage_url')

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

    data, url = await loop.run_in_executor(None, to_run)
    if 'entries' in data:
      data = data['entries'][0]

    if ctx.voice_client and ctx.voice_client.is_playing():
      await ctx.send(embed=create_embed('**Queued up** \"{}\"'.format(data['title'])))
      return {'webpage_url': data['webpage_url'], 'requester': id, 'title': data['title']}
    
    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTS, method='fallback')
    return cls(source, data=data, requester=id)
  
  @classmethod
  async def regather_stream(cls, data, loop):
    loop = loop or asyncio.get_event_loop()
    requester = data['requester']

    to_run = partial(search, query=data['webpage_url'])
    data, url = await loop.run_in_executor(None, to_run)

    return cls(await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTS, method='fallback'), data=data, requester=requester)

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
    while not self.bot.is_closed():
      self.next.clear()

      try:  # Wait for the next song. If we timeout cancel the player and disconnect
        async with timeout(60): # 60 seconds before timing out
          ytdlSource = await self.queue.get()
      except asyncio.TimeoutError:
        log.info('Queue seems to be empty. Cleaning up music player')
        return self.destroy(self.guild)

      if not isinstance(ytdlSource, YTDLSource):
        ''' in case the queue is super long, there's a chance that queued up songs
            have already expired so we'll regather the stream to generate a fresh url'''
        try:
          ytdlSource = await YTDLSource.regather_stream(ytdlSource, loop=self.bot.loop)
        except Exception as e:
          log.warning('There was an error processing a song')
          log.error(e)
          await self.channel.send(embed=create_embed('An error occured!'))
          continue
      
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
    # Disconnect and cleanup music player
    return self.bot.loop.create_task(self.cog.cleanup(guild))

