# customized version of https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34#file-music-py
import asyncio
import discord
import itertools
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

  def __init__(self, source, title, webpage_url, filepath, requester, interaction):
    self.source = source
    self.requester = requester

    self.title = title
    self.webpage_url = webpage_url
    self.filepath = filepath
    self.interaction = interaction

  @classmethod
  async def create(cls, interaction: discord.Interaction, query: str, loop):
    loop = loop or asyncio.get_event_loop()
    to_run = partial(search, query=query)
    id = ''

    try:
      id = interaction.user.id
    except Exception as e:
      if isinstance(e, AttributeError) is False:
        log.error(e)

    title, webpage_url, filepath = await loop.run_in_executor(None, to_run)

    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
      await interaction.channel.send(embed=create_embed('**Queued up** \"{}\"'.format(title)))
    
    source = await discord.FFmpegOpusAudio.from_probe(filepath, **FFMPEG_OPTS, method='fallback')
    return cls(source, title=title, webpage_url=webpage_url, filepath=filepath, requester=id, interaction=interaction)

  @classmethod
  async def replicate(cls, ytdlSource):
    source = await discord.FFmpegOpusAudio.from_probe(ytdlSource.filepath, **FFMPEG_OPTS, method='fallback')
    return cls(source, title=ytdlSource.title, webpage_url=ytdlSource.webpage_url, filepath=ytdlSource.filepath, requester=ytdlSource.requester, interaction=ytdlSource.interaction)

class MusicPlayer:

  __slots__ = ('bot', 'guild', 'channel', 'cog', 'queue', 'next', 'current', 'message', 'replay')

  def __init__(self, interaction: discord.Interaction):
    self.bot = interaction.client
    self.guild = interaction.guild
    self.channel = interaction.channel
    self.cog = interaction.command.extras['cog']

    self.queue = asyncio.Queue()
    self.next = asyncio.Event()

    self.message = None # now playing message
    self.current = None # current YTDLSource
    self.replay = False

    self.bot.loop.create_task(self.player_loop())
  
  def __after(self, e):
    if e:
      log.error(e)
    self.bot.loop.call_soon_threadsafe(self.next.set)
  
  def get_upcoming(self):
    return list(itertools.islice(self.queue._queue, 0, self.queue.qsize()))
  
  # remove an element from the queue given a position
  async def remove(self, pos: int):
    if pos <= 0:
      return

    new_queue = asyncio.Queue()
    current_pos = 0

    while not self.queue.empty():
      item = await self.queue.get()
      current_pos += 1
      if current_pos != pos:
        await new_queue.put(item)
    
    self.queue = new_queue

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

        # wait for audio to finish playing
        await self.next.wait()

        # put the audio back into queue if replay is true
        if self.replay:
          await self.queue.put(await YTDLSource.replicate(ytdlSource))

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
