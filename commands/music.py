# customized from https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34#file-music-py
import discord
import logging
import itertools
from discord.ext import commands

# project imports
from commands.music_player import MusicPlayer
from commands.music_player import YTDLSource
from lib.utils import create_embed

# set up logging
log = logging.getLogger('bot')

class Music(commands.Cog):

  __slots__ = ('bot', 'music_players')

  def __init__(self, bot):
    self.bot = bot
    self.music_players = {}

  async def cleanup(self, guild):
    try:
      await guild.voice_client.disconnect()
    except AttributeError:
      pass

    try:
      del self.music_players[guild.id]
    except KeyError:
      pass

  def get_music_player(self, ctx=None, guild=None):
    music_player = None

    if ctx:
      try:
        music_player = self.music_players[ctx.guild.id]
      except KeyError:
        music_player = MusicPlayer(ctx)
        self.music_players[ctx.guild.id] = music_player
    
    elif guild:
      try:
        music_player = self.music_players[guild.id]
      except KeyError:
        pass
    
    return music_player

  def music_player_exists(self, guild=None):
    try:
      self.music_players[guild.id]
      return True
    except KeyError:
      pass

    return False

  async def __verify(self, ctx):
    if ctx.voice_client is None:
      await ctx.send(embed=create_embed('<@{}> I am not connected to a voice channel'.format(ctx.author.id)))
      return False
    if ctx.author.voice is None:
      await ctx.send(embed=create_embed('<@{}> You are not connected to a voice channel'.format(ctx.author.id)))
      return False
    if ctx.author.voice.channel != ctx.voice_client.channel:
      await ctx.send(embed=create_embed('<@{}> You must be in the same voice channel as me'.format(ctx.author.id)))
      return False
      
    return True

  @commands.command() # returns True on success
  async def connect(self, ctx, channel: discord.VoiceChannel=None):
    if not channel:
      try:
        channel = ctx.author.voice.channel
      except Exception as e:
        if isinstance(e, AttributeError):
          await ctx.send(embed=create_embed('<@{}> Please connect to a voice channel first'.format(ctx.author.id)))
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
    vc = ctx.voice_client

    if not vc:
      if await ctx.invoke(self.connect) is False:
        return

    await ctx.trigger_typing()  # typing signal on Discord
    
    music_player = self.get_music_player(ctx=ctx)
    ytdlSource = await YTDLSource.create(ctx, search, loop=self.bot.loop)

    await music_player.queue.put(ytdlSource)

  @commands.command()
  async def stop(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=create_embed('<@{}> I am not in a voice channel'.format(ctx.author.id)))

    if self.music_player_exists(ctx.guild):
      music_player = self.get_music_player(ctx)
      music_player.clear_queue()
      await ctx.send(embed=create_embed('<@{}> stopped the music'.format(ctx.author.id)))
    
    await vc.disconnect()

  @commands.command()
  async def pause(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=create_embed('<@{}> I am not in a voice channel'.format(ctx.author.id)))

    if vc.is_playing():
      vc.pause()
      return await ctx.send(embed=create_embed('<@{}> paused the music'.format(ctx.author.id)))

    await ctx.send(embed=create_embed('<@{}> music is already paused'.format(ctx.author.id)))

  @commands.command()
  async def resume(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=create_embed('<@{}> I am not in a voice channel'.format(ctx.author.id)))

    if vc.is_playing() is False:
      vc.resume()
      return await ctx.send(embed=create_embed('<@{}> resumed the music'.format(ctx.author.id)))

    await ctx.send(embed=create_embed('<@{}> music is already playing'.format(ctx.author.id)))

  @commands.command(name='current_song', aliases=['currentsong'])
  async def current_song(self, ctx):
    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=create_embed('<@{}> I am not playing music'.format(ctx.author.id)))
    
    music_player = self.get_music_player(ctx=ctx)
    if music_player.current is None:
      return await ctx.send(embed=create_embed('<@{}> I am not playing music'.format(ctx.author.id)))
    
    try:
      await music_player.message.delete()
    except Exception as e:
      log.error(e)
      pass
    
    ytdlSource = music_player.get_current()
    response = None
    # title attribute seems to be weirdly inconsistent
    try:
      response = '**Now Playing:**\n\"{}\" requested by <@{}>'.format(ytdlSource.title, ytdlSource.requester)
    except:
      try:
        response = '**Now Playing:**\n\"{}\" requested by <@{}>'.format(ytdlSource['title'], ytdlSource.requester)
      except Exception as e:
        log.error(e)
        return await ctx.send(embed=create_embed('Sorry! An error occured when retrieving current song information'))

    music_player.message = await ctx.send(embed=create_embed(response))

  @commands.command(name='queue')
  async def queue_info(self, ctx):
    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=create_embed('<@{}> I am not playing music'.format(ctx.author.id)))

    music_player = self.get_music_player(ctx=ctx)
    if music_player.queue.empty():
      return await ctx.send(embed=create_embed('<@{}> There are no queued songs'.format(ctx.author.id)))

    upcoming = list(itertools.islice(music_player.queue._queue, 0, music_player.queue.qsize()))
    
    format = None
    # it seems like the "title" attribute is inconsistent :(
    try:
      format = '\n'.join('**{}.** {}'.format(index+1, ytdlSource.title) for index, ytdlSource in enumerate(upcoming))
    except:
      try:
        format = '\n'.join('**{}.** {}'.format(index+1, ytdlSource['title']) for index, ytdlSource in enumerate(upcoming))
      except Exception as e:
        log.error(e)
        return await ctx.send(embed=create_embed('Sorry! An error occured when retrieving queue information'))

    embed = discord.Embed(title='Upcoming - Next {}'.format(len(upcoming)), description=format)
    await ctx.send(embed=embed)

  @commands.command()
  async def skip(self, ctx):
    if await self.__verify(ctx) is False:
      return

    vc = ctx.voice_client

    if not vc or not vc.is_connected():
      return await ctx.send(embed=create_embed('<@{}> I am not playing music'.format(ctx.author.id)))
    
    # check if music is paused before checking if music is playing
    if vc.is_paused():
      pass
    elif not vc.is_playing():
      return await ctx.send(embed=create_embed('<@{}> there are no more songs to play'.format(ctx.author.id)))
    
    vc.stop()
    await ctx.send(embed=create_embed('<@{}> skipped the song'.format(ctx.author.id)))
  
  @commands.Cog.listener()
  async def on_command_error(self, ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
      error_str_arr = str(error).split(' ')
      if (error_str_arr[0] == 'search'):
        try:
          await ctx.send(embed=create_embed('<@{}> Please specify a query'.format(ctx.author.id)))
        except Exception as e:
          log.error(e)

def setup(bot):
  try:
    bot.add_cog(Music(bot))
    log.info('Successfully set up music commands')
  except Exception as e:
    log.warning('Error occured when setting up music commands')
    log.error(e)
