import discord
import requests
import logging
from youtube_dl import YoutubeDL
from discord.ext import commands

# set up logging
log = logging.getLogger('bot')

def search(query):
  with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
    try: requests.get(query)
    except: info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    else: info = ydl.extract_info(query, download=False)
  return (info, info['formats'][0]['url'])

class music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.FFMPEG_OPTIONS = {
      'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
      'options': '-vn'
    }

  def _create_embed(self, message):
    embed = discord.Embed(description=message)
    return embed

  async def _verify(self, ctx):
    try:
      if ctx.voice_client is None:
        await ctx.send(embed=self._create_embed('<@{}> I am not connected to a voice channel'.format(ctx.author.id)))
        return False
      if ctx.author.voice is None:
        await ctx.send(embed=self._create_embed('<@{}> You are not connected to a voice channel'.format(ctx.author.id)))
        return False
      if ctx.author.voice.channel != ctx.voice_client.channel:
        await ctx.send(embed=self._create_embed('<@{}> You must be in the same voice channel as me'.format(ctx.author.id)))
        return False
      return True
    except Exception as e:
      log.error(e)

  async def _join(self, ctx):
    if ctx.author.voice is None:
      await ctx.send(embed=self._create_embed('<@{}> Please connect to a voice channel first'.format(ctx.author.id)))
      return False

    voice_channel = ctx.author.voice.channel
    try:
      if ctx.voice_client is None:  # if bot is not in a voice channel then connect to author's voice channel
        await voice_channel.connect()
      elif ctx.voice_client != voice_channel: # if bot is already in a voice channel, then move to the author's voice channel
        await ctx.voice_client.move_to(voice_channel)
      return True
    except Exception as e:
      log.error(e)
      return False

  @commands.command()
  async def play(self, ctx, query):
    info, source = search(query)
    try:
      await self._join(ctx)
      if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
      ctx.voice_client.play(await discord.FFmpegOpusAudio.from_probe(source, **self.FFMPEG_OPTIONS))
      await ctx.send(embed=self._create_embed('<@{}> Now playing \"{}\"'.format(ctx.author.id, info['title'])))
    except Exception as e:
      log.error(e)
  
  @commands.command()
  async def stop(self, ctx):
    verify = await self._verify(ctx)
    if verify is False:
      return
    try:
      await ctx.voice_client.disconnect()
    except Exception as e:
      log.error(e)
    
  
  @commands.command()
  async def pause(self, ctx):
    verify = await self._verify(ctx)
    if verify is False:
      return
    try:
      ctx.voice_client.pause()
      await ctx.send(embed=self._create_embed('Paused'))
    except Exception as e:
      log.error(e)
  
  @commands.command()
  async def resume(self, ctx):
    verify = await self._verify(ctx)
    if verify is False:
      return
    try:
      ctx.voice_client.resume()
      await ctx.send(embed=self._create_embed('Resumed'))
    except Exception as e:
      log.error(e)
  
  @commands.Cog.listener()
  async def on_command_error(self, ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
      error_str_arr = str(error).split(' ')
      if (error_str_arr[0] == 'query'):
        try:
          await ctx.send(embed=self._create_embed('<@{}> Please specify a URL'.format(ctx.author.id)))
        except Exception as e:
          log.error(e)

def setup(bot):
  try:
    bot.add_cog(music(bot))
    log.info('Successfully set up music commands')
  except Exception as e:
    log.info('Error occured when setting up music commands\n')
    log.error(e)
