import discord
from discord import player
import requests
import logging
import itertools
from discord.ext import commands
from youtube_dl import YoutubeDL

from commands.music_player import MusicPlayer
from commands.music_player import YTDLSource

# set up logging
log = logging.getLogger('bot')

ytdlopts = {
  'format': 'bestaudio/best', 
  'noplaylist': True, 
  'nocheckcertificate': True, 
  'source_address': '0.0.0.0'
}

def search(query):
  with YoutubeDL(ytdlopts) as ydl:
    try: requests.get(query)
    except: info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    else: info = ydl.extract_info(query, download=False)
  return (info, info['formats'][0]['url'])

class Music(commands.Cog):

  __slots__ = ('bot', 'music_players', 'FFMPEG_OPTIONS')

  def __init__(self, bot):
    self.bot = bot
    self.music_players = {}
    self.FFMPEG_OPTIONS = {
      'before_options': '-nostdin', 
      'options': '-vn'
    }

  async def cleanup(self, guild):
    try:
      await guild.voice_client.disconnect()
    except AttributeError:
      pass

    try:
      del self.players[guild.id]
    except KeyError:
      pass

  async def __local_check(self, ctx):
    if not ctx.guild:
      raise commands.NoPrivateMessage
    return True

  def __create_embed(self, message):
    embed = discord.Embed(description=message)
    return embed

  def get_music_player(self, ctx):
    try:
      music_player = self.music_players[ctx.guild.id]
    except KeyError:
      music_player = MusicPlayer(ctx)
      self.music_players[ctx.guild.id] = music_player
    
    return music_player

  async def __verify(self, ctx):
    if ctx.voice_client is None:
      await ctx.send(embed=self.__create_embed('<@{}> I am not connected to a voice channel'.format(ctx.author.id)))
      return False
    if ctx.author.voice is None:
      await ctx.send(embed=self.__create_embed('<@{}> You are not connected to a voice channel'.format(ctx.author.id)))
      return False
    if ctx.author.voice.channel != ctx.voice_client.channel:
      await ctx.send(embed=self.__create_embed('<@{}> You must be in the same voice channel as me'.format(ctx.author.id)))
      return False
      
    return True

  @commands.command() # returns True on success
  async def connect(self, ctx, *, channel: discord.VoiceChannel=None):
    if not channel:
      try:
        channel = ctx.author.voice.channel
      except Exception as e:
        if isinstance(e, AttributeError):
          await ctx.send(embed=self.__create_embed('<@{}> Please connect to a voice channel first'.format(ctx.author.id)))
        else:
          log.error(e)
        return False

    vc = ctx.voice_client

    if vc:
      if vc.channel.id == channel.id:
        return True
      try:
        await vc.move_to(channel)
      except Exception as e:
        log.error(e)
        return False
    else:
      try:
        await channel.connect()
      except Exception as e:
        log.error(e)
        return False
    
    return True

  @commands.command()
  async def play(self, ctx, *, search: str):
    await ctx.trigger_typing()  # typing signal on Discord

    vc = ctx.voice_client
    
    music_player = self.get_music_player(ctx)

    source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)

    if not vc:
      if await ctx.invoke(self.connect) is False:
        return

    await music_player.queue.put(source)

  @commands.command()
  async def stop(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=self.__create_embed('<@{}> I am not in a voice channel'.format(ctx.author.id)))

    await vc.disconnect()
    await ctx.send(embed=self.__create_embed('<@{}> stopped the music'.format(ctx.author.id)))
  
  @commands.command()
  async def pause(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=self.__create_embed('<@{}> I am not in a voice channel'.format(ctx.author.id)))

    vc.pause()
    await ctx.send(embed=self.__create_embed('<@{}> paused the music'.format(ctx.author.id)))

  @commands.command()
  async def resume(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=self.__create_embed('<@{}> I am not in a voice channel'.format(ctx.author.id)))

    vc.resume()
    await ctx.send(embed=self.__create_embed('<@{}> resumed the music'.format(ctx.author.id)))

  @commands.command(name='current_song', aliases=['currentsong'])
  async def current_song(self, ctx):
    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=self.__create_embed('<@{}> I am not playing music'.format(ctx.author.id)))
    
    music_player = self.get_music_player(ctx)
    if music_player.current is None:
      return await ctx.send(embed=self.__create_embed('<@{}> I am not playing music'.format(ctx.author.id)))
    
    try:
      await music_player.message.delete()
    except Exception as e:
      log.error(e)
      pass
    
    music_player.message = '**Now Playing:**\n\"{}\" requested by <@{}>'.format(vc.source.title, vc.source.requester)
    await ctx.send(embed=self.__create_embed(music_player.message))

  @commands.command(name='queue')
  async def queue_info(self, ctx):
    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=self.__create_embed('<@{}> I am not playing music'.format(ctx.author.id)))

    music_player = self.get_music_player(ctx)
    if music_player.queue.empty():
      return await ctx.send(embed=self.__create_embed('<@{}> There are no queued songs'.format(ctx.author.id)))
    
    upcoming_songs = list(itertools.islice(music_player.queue._queue, 0, music_player.queue.qsize()))

    format = '\n'.join('**{}**'.format(song['title']) for song in upcoming_songs)
    embed = discord.Embed(title='Upcoming - Next {}'.format(len(upcoming_songs)), description=format)

    await ctx.send(embed=embed)

  @commands.command()
  async def skip(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=self.__create_embed('<@{}> I am not playing music'.format(ctx.author.id)))
    
    # check if music is paused before checking if music is playing
    if vc.is_paused():
      pass
    elif not vc.is_playing():
      return
    
    vc.stop()
    await ctx.send(embed=self.__create_embed('<@{}> skipped the song'.format(ctx.author.id)))
  
  @commands.Cog.listener()
  async def on_command_error(self, ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
      error_str_arr = str(error).split(' ')
      if (error_str_arr[0] == 'search'):
        try:
          await ctx.send(embed=self.__create_embed('<@{}> Please specify a query'.format(ctx.author.id)))
        except Exception as e:
          log.error(e)

def setup(bot):
  try:
    bot.add_cog(Music(bot))
    log.info('Successfully set up music commands')
  except Exception as e:
    log.warning('Error occured when setting up music commands')
    log.error(e)
