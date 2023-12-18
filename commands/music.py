# customized from https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34#file-music-py
import discord
from discord import app_commands
from discord.ext import commands

# project imports
from commands.music_player import MusicPlayer
from commands.music_player import YTDLSource
from lib.utils import create_embed
from lib.utils import delete_temp_dir

class Music(commands.Cog):

  __slots__ = ('bot', 'music_players')

  def __init__(self, bot, log):
    self.bot = bot
    self.log = log
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

  def get_music_player(self, interaction: discord.Interaction):
    music_player = None
    try:
      music_player = self.music_players[interaction.guild_id]
    except KeyError:
      interaction.command.extras['cog'] = self
      music_player = MusicPlayer(interaction)
      self.music_players[interaction.guild_id] = music_player
    
    return music_player

  def music_player_exists(self, guild):
    try:
      self.music_players[guild.id]
      return True
    except KeyError:
      pass

    return False

  async def __verify(self, interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
      await interaction.response.send_message(embed=create_embed('<@{}> I am not connected to a voice channel'.format(interaction.user.id)))
      return False
    if interaction.user.voice is None:
      await interaction.response.send_message(embed=create_embed('<@{}> You are not connected to a voice channel'.format(interaction.user.id)))
      return False
    if interaction.user.voice.channel != interaction.guild.voice_client.channel:
      await interaction.response.send_message(embed=create_embed('<@{}> You must be in the same voice channel as me'.format(interaction.user.id)))
      return False
      
    return True

  @app_commands.command(name="play", description="Plays music from a search query or URL")
  @app_commands.describe(search="The YouTube search query or URL (YouTube/Soundcloud)")
  async def play(self, interaction: discord.Interaction, search: str):
    vc = interaction.guild.voice_client

    if interaction.user.voice is None:
      return await interaction.response.send_message(embed=create_embed('<@{}> Please connect to a voice channel first'.format(interaction.user.id)))

    if vc is None:
      try:
        await interaction.user.voice.channel.connect()
      except Exception as e:
        self.log.error(e)
        return await interaction.response.send_message(embed=create_embed('<@{}> I could not connect to your voice channel'.format(interaction.user.id)))

    if vc and vc.channel.id != interaction.user.voice.channel.id:
      return await interaction.response.send_message(embed=create_embed('<@{}> You must be in the same voice channel as me'.format(interaction.user.id)))

    await interaction.response.defer(ephemeral=True, thinking=True)
    
    music_player = self.get_music_player(interaction=interaction)
    ytdlSource = await YTDLSource.create(interaction, search, loop=self.bot.loop)
    await music_player.queue.put(ytdlSource)

    return await interaction.followup.send('Queued up {}'.format(search), ephemeral=True, silent=True)

  @app_commands.command(name="replay", description="Toggles the replay of the entire queue")
  async def replay(self, interaction: discord.Interaction):
    if await self.__verify(interaction) is False:
      return

    vc = interaction.guild.voice_client

    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not in a voice channel'.format(interaction.user.id)))
  
    if self.music_player_exists(interaction.guild):
      music_player = self.get_music_player(interaction=interaction)
      music_player.replay = not music_player.replay

      if music_player.replay:
        await interaction.response.send_message(embed=create_embed('<@{}> enabled replay'.format(interaction.user.id)))
      else:
        await interaction.response.send_message(embed=create_embed('<@{}> disabled replay'.format(interaction.user.id)))

  @app_commands.command(name="stop", description="Stops music and disconnects the bot")
  async def stop(self, interaction: discord.Interaction):
    if await self.__verify(interaction) is False:
      return

    vc = interaction.guild.voice_client

    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not in a voice channel'.format(interaction.user.id)))

    if self.music_player_exists(interaction.guild):
      music_player = self.get_music_player(interaction=interaction)
      music_player.clear_queue()

      try:
        delete_temp_dir()
      except Exception as e:
        self.log.error(e)

      await interaction.response.send_message(embed=create_embed('<@{}> stopped the music'.format(interaction.user.id)))
    
    await vc.disconnect()

  @app_commands.command(name="pause", description="Pauses the music")
  async def pause(self, interaction: discord.Interaction):
    if await self.__verify(interaction) is False:
      return

    vc = interaction.guild.voice_client

    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not in a voice channel'.format(interaction.user.id)))

    if vc.is_playing():
      vc.pause()
      return await interaction.response.send_message(embed=create_embed('<@{}> paused the music'.format(interaction.user.id)))

    await interaction.response.send_message(embed=create_embed('<@{}> music is already paused'.format(interaction.user.id)))

  @app_commands.command(name="resume", description="Resumes the music")
  async def resume(self, interaction: discord.Interaction):
    if await self.__verify(interaction) is False:
      return

    vc = interaction.guild.voice_client

    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not in a voice channel'.format(interaction.user.id)))

    if vc.is_playing() is False:
      vc.resume()
      return await interaction.response.send_message(embed=create_embed('<@{}> resumed the music'.format(interaction.user.id)))

    await interaction.response.send_message(embed=create_embed('<@{}> music is already playing'.format(interaction.user.id)))

  @app_commands.command(name="currentsong", description="Displays the current song")
  async def current_song(self, interaction: discord.Interaction):
    vc = interaction.guild.voice_client

    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not playing music'.format(interaction.user.id)))
    
    music_player = self.get_music_player(interaction=interaction)
    if music_player.current is None:
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not playing music'.format(interaction.user.id)))
    
    try:
      await music_player.message.delete()
    except Exception as e:
      self.log.error(e)
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
        self.log.error(e)
        return await interaction.response.send_message(embed=create_embed('Sorry! An error occured when retrieving current song information'))

    music_player.message = await interaction.response.send_message(embed=create_embed(response))

  @app_commands.command(name="queue", description="Displays the music queue")
  async def queue_info(self, interaction: discord.Interaction):
    vc = interaction.guild.voice_client

    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not playing music'.format(interaction.user.id)))

    music_player = self.get_music_player(interaction=interaction)
    if music_player.queue.empty():
      if music_player.replay:
        return await interaction.response.send_message(embed=create_embed('<@{}> There are no queued songs. The current song will replay'.format(interaction.user.id)))
      else:
        return await interaction.response.send_message(embed=create_embed('<@{}> There are no queued songs'.format(interaction.user.id)))

    upcoming = music_player.get_upcoming()

    format = None
    # it seems like the "title" attribute is inconsistent :(
    try:
      format = '\n'.join('**{}.** {}'.format(index+1, ytdlSource.title) for index, ytdlSource in enumerate(upcoming))
    except:
      try:
        format = '\n'.join('**{}.** {}'.format(index+1, ytdlSource['title']) for index, ytdlSource in enumerate(upcoming))
      except Exception as e:
        self.log.error(e)
        return await interaction.response.send_message(embed=create_embed('Sorry! An error occured when retrieving queue information'))
    
    replay_message = "Replay is enabled" if music_player.replay else "Replay is disabled"
    embed = discord.Embed(title='Upcoming - Next {} ({})'.format(len(upcoming), replay_message), description=format)
    await interaction.response.send_message(embed=embed)

  @app_commands.command(name="remove", description="Removes a song from the queue")
  @app_commands.describe(position="The position of the song in the queue to remove")
  async def remove(self, interaction: discord.Interaction, position: int):
    if await self.__verify(interaction) is False:
      return
    
    vc = interaction.guild.voice_client
    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not playing music'.format(interaction.user.id)))
    
    music_player = self.get_music_player(interaction=interaction)
    if music_player.queue.empty():
      return await interaction.response.send_message(embed=create_embed('<@{}> There are no queued songs'.format(interaction.user.id)))

    upcoming = music_player.get_upcoming()
    if position <= 0 or len(upcoming) < position:
      return await interaction.response.send_message(embed=create_embed('<@{}> **{}** is not a valid position in the queue'.format(interaction.user.id, position)))
      
    removed = upcoming[position - 1]
    await music_player.remove(position)

    return await interaction.response.send_message(embed=create_embed('<@{}> removed **{}** from the queue'.format(interaction.user.id, removed.title)))

  @app_commands.command(name="skip", description="Skips the current song")
  async def skip(self, interaction: discord.Interaction):
    if await self.__verify(interaction) is False:
      return

    vc = interaction.guild.voice_client

    if not vc or not vc.is_connected():
      return await interaction.response.send_message(embed=create_embed('<@{}> I am not playing music'.format(interaction.user.id)))
    
    # check if music is paused before checking if music is playing
    if vc.is_paused():
      pass
    elif not vc.is_playing():
      return await interaction.response.send_message(embed=create_embed('<@{}> there are no more songs to play'.format(interaction.user.id)))
    
    vc.stop()
    await interaction.response.send_message(embed=create_embed('<@{}> skipped the song'.format(interaction.user.id)))

async def setup(bot, log, guild_id):
  try:
    await bot.add_cog(Music(bot, log), guilds=[discord.Object(id=guild_id)])
  except Exception as e:
    log.error(e)
