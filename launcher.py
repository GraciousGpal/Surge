import asyncio
import random
import sys

import discord
from discord.ext import commands

from Core import dataCheck, Guild, session, User, emb, create_full_table
from Core.preboot import *


def get_prefix(bot, message):
    """This allows custom prefix per server."""

    # Notice how you can use spaces in prefixes. Try to keep them simple though.
    prefixz = bot.master[message.guild.id]["prefix"]
    # prefixz = [session.query(Guild).filter_by(id=message.guild.id).first().prefix]
    if prefixz[0] is None:
        prefixz = ['+']

    # Check to see if we are outside of a guild. e.g DM's etc.
    if not message.guild:
        # Only allow + to be used in DMs
        return ['+']

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return commands.when_mentioned_or(*prefixz)(bot, message)


def load_mods(extension: str, self):
    try:
        bot.load_extension(extension)
        logging.info("[{}] Loaded!.".format(extension))
        self.loaded = [f for f in self.cogs]
        return [True, None]
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        logging.error('Failed to load extension {}\n{}'.format(extension, exc))
        return [False, e]


# Main Bot Class
class MyClient(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  #
        self.Settings = {}  # Bot Settings
        self.master = {}
        self.loaded = []  # Lists loaded modules

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.statuschange())

    async def statuschange(self):
        await self.wait_until_ready()
        message_list = [" {} people!.", "Ping pong with {} the crew", "Laser Tag with {} People"]
        while True:
            await self.change_presence(
                activity=discord.Game(name=random.choice(message_list).format(session.query(User).count())))
            # logging.info(self.loaded)
            await asyncio.sleep(10)

    async def on_ready(self):
        #create_full_table(self)
        checksettings(self)

        # Initial module Loading..
        plist = [f for f in os.listdir('modules') if ".py" in f]
        if '__init__.py' in plist:
            plist.remove("__init__.py")
        [load_mods('modules' + "." + f.replace(".py", ""), self) for f in plist]

        # Check Data integrity
        dataCheck(self)

        logging.info("______________________________________________")
        logging.info(f'Logged in as: {bot.user.name} - {bot.user.id}')
        logging.info(f"Framework Version: {discord.__version__}")
        logging.info("______________________________________________")
        logging.info(f'Successfully logged in and booted...!')

    async def on_command_error(self, ctx, error):
        if "The global check functions for command" in str(error):
            await ctx.send(
                "```Python\n Install {} package to use this command ! \n Request your server admin to install this module.```".format(
                    ctx.command.cog_name))
        else:
            await ctx.message.channel.send("```" + str(error) + "```")


# Declaring Client & command prefixes/descriptions..
bot = MyClient(command_prefix=get_prefix, description='Get Some when you need it!')


@bot.command(hidden=True)
async def set_prefix(ctx, message):
    """
    Set the prefix for bot commands.
    :param ctx:
    :param message:
    :return:
    """
    row = session.query(Guild).filter(
        Guild.id == ctx.guild.id).first()
    row.prefix = message
    session.commit()
    try:
        bot.master[ctx.guild.id]["prefix"] = message
    except Exception as e:
        bot.master[ctx.guild.id] = {}
        bot.master[ctx.guild.id]["prefix"] = message
    await ctx.send('```Bot Command Prefix set to  : {}```'.format(message))


@bot.command(hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    """
    Save SQL Data and turn off the bot
    :param ctx:
    :return:
    """
    logging.warning('{} with id {} in server : {} has initiated bot shutdown!.'.format(ctx.author.name, ctx.author.id,
                                                                                       ctx.guild.id))
    await ctx.send(emb('Shutting Down....I will see you on the other side.'))
    session.commit()
    session.close()
    sys.exit()


@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.unload_extension("modules." + extension)
    except  ModuleNotFoundError as e:
        logging.error(e)
    try:
        bot.load_extension("modules." + extension)
        await ctx.message.channel.send("Module [{}] reloaded!".format(extension))
    except (AttributeError, ImportError) as e:
        await ctx.message.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))


@bot.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension("modules." + extension)
        await ctx.message.channel.send("Module [{}] loaded!".format(extension))
    except (AttributeError, ImportError) as e:
        await ctx.message.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))


@bot.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension("modules." + extension)
        await ctx.message.channel.send("Module [{}] unloaded!".format(extension))
    except  ModuleNotFoundError as e:
        logging.error(e)


@bot.command(hidden=True)
@commands.is_owner()
async def reboot(ctx):
    logging.warning(
        '{} with id {} in server : {} has initiated bot Reboot!.'.format(ctx.author.name, ctx.author.id, ctx.guild.id))
    session.commit()
    session.close()
    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)


# Orginal
os.environ['DISCORDAPI'] = 'NDQ2OTUyNzE2NzM3MDUyNjcy.DerJCA.AuN65sODFObrTeBUY3Ggovw3l1U'
# Quinny
# os.environ['DISCORDAPI'] = 'NTAwNTI4NzY0MDk5NDkzODkw.DqMJag.lHqZmQCQVyFpS5lEJfHpqahawaQ'
os.environ['compiler_clientId'] = '14444bf7dedc244050166a77295bc61c'
os.environ[
    'compiler_clientSecret'] = "b9d5a80a216692a45d2d26ef294a20d43ffa4762b54ea980de9e28cffda43fcf"
os.environ['DROPBOXAPI'] = ""
bot.run(os.environ['DISCORDAPI'], bot=True, reconnect=True)
