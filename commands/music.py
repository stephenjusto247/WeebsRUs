import discord
import requests
from youtube_dl import YoutubeDL
from discord.ext import commands

class music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  def _create_embed(self, message):
    embed = discord.Embed(description=message)
    return embed

  def _search(self, query):
    with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
      try: requests.get(query)
      except: info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
      else: info = ydl.extract_info(query, download=False)
    return (info['formats'][0]['url'])

  async def _verify(self, ctx):
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

  @commands.command()
  async def play(self, ctx, query):
    if ctx.author.voice is None:
      await ctx.send(embed=self._create_embed('<@{}> Please connect to a voice channel first'.format(ctx.author.id)))
      return
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
      ctx.voice_client.stop()
      await ctx.voice_client.move_to(voice_channel)
    
    FFMPEG_OPTIONS = {
      'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
      'options': '-vn'
    }
    source = self._search(query)
    await voice_channel.connect()
    try:
      ctx.voice_client.play(await discord.FFmpegOpusAudio.from_probe(source, **FFMPEG_OPTIONS))
      ctx.voice_client.is_playing()
    except Exception as e:
      print(str(e))
  
  @commands.command()
  async def disconnect(self, ctx):
    verify = await self._verify(ctx)
    if verify is False:
      return
    await ctx.voice_client.disconnect()
    
  
  @commands.command()
  async def pause(self, ctx):
    verify = await self._verify(ctx)
    if verify is False:
      return
    await ctx.voice_client.pause()
    await ctx.send(embed=self._create_embed('Paused'))
  
  @commands.command()
  async def resume(self, ctx):
    verify = await self._verify(ctx)
    if verify is False:
      return
    await ctx.voice_client.resume()
    await ctx.send(embed=self._create_embed('Resumed'))
  
  @commands.Cog.listener()
  async def on_command_error(self, ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
      error_str_arr = str(error).split(' ')
      if (error_str_arr[0] == 'query'):
        await ctx.send(embed=self._create_embed('<@{}> Please specify a URL'.format(ctx.author.id)))

def setup(bot):
  try:
    bot.add_cog(music(bot))
    print('Successfully set up music commands')
  except Exception as e:
    print('Error occured when setting up music commands\n')
    print(e)
