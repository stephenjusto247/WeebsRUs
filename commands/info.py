import discord
import sys
from discord import app_commands
from discord.ext import commands
from prettytable import PrettyTable

# project imports
from lib.utils import create_embed

# Checks if user set a prefix
if (len(sys.argv) > 1 and len(sys.argv[1]) == 1):
    COMMAND_PREFIX = sys.argv[1]
else:
    COMMAND_PREFIX = '$'

class Info(commands.Cog):
  def __init__(self, bot, log):
    self.bot = bot
    self.log = log

  @app_commands.command(name="help", description="Displays a list of commands")
  async def help(self, interaction: discord.Interaction):
    try:
      table = PrettyTable()
      table.field_names = ['command', 'description']
      rows = [
        ['play', 'Play music from YouTube source'],
        ['stop', 'Stops music and disconnects bot'],
        ['pause', 'Pauses music'],
        ['resume', 'Resumes music'],
        ['currentsong', 'Display current song'],
        ['skip', 'Skips the current song'],
        ['queue', 'Get queue info'],
        ['replay', 'Enable/disable replay of the entire queue'],
        ['remove', 'Remove a song from the queue']
      ]
      for row in rows:
        row[0] = COMMAND_PREFIX + row[0]
        table.add_row(row)
      response = table.get_string()
      await interaction.response.send_message(embed=create_embed('**command list**\n```\n{}\n```'.format(response)))
    except Exception as e:
      self.log.error(e)

async def setup(bot, log, guild_id):
  bot.remove_command('help')

  try:    
    await bot.add_cog(Info(bot, log), guilds=[discord.Object(id=guild_id)])
  except Exception as e:
    log.error(e)
