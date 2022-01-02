# credit to https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34#file-music-py

import discord
import logging
import asyncio
from async_timeout import timeout
from youtube_dl import YoutubeDL
from functools import partial

# set up logging
log = logging.getLogger('bot')

YTDL_OPTS = {
  'format': 'bestaudio/best', 
  'noplaylist': True, 
  'nocheckcertificate': True, 
  'source_address': '0.0.0.0'
}

FFMPEG_OPTS = {
  'before_options': '-nostdin', 
  'options': '-vn'
}

ytdl = YoutubeDL(YTDL_OPTS)

class YTDLSource(discord.PCMVolumeTransformer):

  def __init__(self, source, *, data, requester):
    super().__init__(source)
    # self.source = source
    self.requester = requester

    self.title = data.get('title')
    self.web_url = data.get('webpage_url')
  
  def __getitem__(self, item: str):
    return self.__getattribute__(item)

  @classmethod
  async def create_source(cls, ctx, search: str, loop):
    loop = loop or asyncio.get_event_loop()

    to_run = partial(ytdl.extract_info, url=search, download=False)
    data = await loop.run_in_executor(None, to_run)
    if 'entries' in data:
      # take first item from a playlist
      data = data['entries'][0]

    source = discord.FFmpegPCMAudio(data['formats'][0]['url'], **FFMPEG_OPTS)
    
    if ctx.voice_client and ctx.voice_client.is_playing():
      await ctx.send('Added \"{}\" to the Queue.'.format(data['title']))

    return cls(source, data=data, requester=ctx.author)
  
  @classmethod
  async def regather_stream(cls, data, *, loop):
    loop = loop or asyncio.get_event_loop()
    requester = data['requester']

    to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
    data = await loop.run_in_executor(None, to_run)

    return cls(discord.FFmpegPCMAudio(data['url'], **FFMPEG_OPTS), data=data, requester=requester)

class MusicPlayer:

  __slots__ = ('bot', 'guild', 'channel', 'cog', 'queue', 'next', 'current', 'message', 'volume')

  def __init__(self, ctx):
    self.bot = ctx.bot
    self.guild = ctx.guild
    self.channel = ctx.channel
    self.cog = ctx.cog

    self.queue = asyncio.Queue()
    self.next = asyncio.Event()

    self.message = None # now playing message
    self.volume = 0.5
    self.current = None

    self.bot.loop.create_task(self.player_loop())
  
  def __after(self, e):
    if e:
      log.error(e)
    self.bot.loop.call_soon_threadsafe(self.next.set)

  async def player_loop(self):
    while not self.bot.is_closed():
      self.next.clear()

      try:  # Wait for the next song. If we timeout cancel the player and disconnect
        async with timeout(60): # 60 seconds
          source = await self.queue.get()
      except asyncio.TimeoutError:
        return self.destroy(self.guild)

      if not isinstance(source, YTDLSource):
        # Source was probably a stream (not downloaded)
        # So we should regather to prevent stream expiration
        try:
          source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
        except Exception as e:
          log.warning('There was an error processing a song')
          log.error(e)
          await self.channel.send('There was an error processing the song')
          continue
      
      source.volume = self.volume
      self.current = source

      self.guild.voice_client.play(source, after=self.__after)
      self.message = await self.channel.send('**Now Playing:**\n\"{}\" requested by {}'.format(source.title, source.requester))

      await self.next.wait()

      source.cleanup()
      self.current = None

      try:
        # We are no longer playing this song
        await self.message.delete()
      except discord.HTTPException:
        pass
  
  def destroy(self, guild):
    # Disconnect and cleanup music player
    return self.bot.loop.create_task(self.cog.cleanup(guild))

