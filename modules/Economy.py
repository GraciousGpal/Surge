import asyncio
import logging
from datetime import datetime

import discord
from discord import Embed
from discord.ext import commands
from prettytable import PrettyTable
from sqlalchemy import exists

from Core import transaction, search, Query, create_player, emb, emoji_norm, Character, Item, Inventory, session

logg = logging.getLogger(__name__)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Description = "Moolah Runs the World!, Adds Economy to the Server."
        self.provision = self.bot.loop.create_task(self.VresourceDist())

    @commands.command()
    async def profile(self, ctx, member=None):
        """
        View your own data and that of others.
        """
        """
        Gets User Info
        """
        if member is None:
            member = ctx.author
        else:
            member = await search(ctx, member)
        User = Query(obj=member).get()
        Player = Query(types="player", obj=member).get()

        if member is not None:
            embed = Embed(title="{}".format(member.name), color=(member.top_role.color))
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="Nick", value=member.nick, inline=True)
            moolah = User.moolah if User is not None else "Error"
            embed.add_field(name="Moolah", value=moolah, inline=True)
            if Player.profession is None:
                embed.set_footer(text="Profession Not Set! {}-{}".format(member.id, str(member.joined_at)[:16]))

            if Player.profession is not None:
                embed.add_field(name="Stats", value="▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁", inline=False)
                embed.add_field(name="Profession", value=Player.profession, inline=True)
                embed.add_field(name="Level", value=Player.level, inline=True)
                embed.add_field(name="Exp", value=Player.exp, inline=True)
                embed.add_field(name="Power", value=Player.atk, inline=True)
                embed.add_field(name="Mind", value=Player.defence, inline=True)
                embed.set_footer(text="{}-{}".format(member.id, str(member.joined_at)[:16]))

            await ctx.send(embed=embed)

            if Player is None:
                await ctx.send("```You have not created a character! {}create to create a character```".format(
                    self.bot.master[ctx.guild.id]["prefix"][0]))
        else:
            await ctx.send("**{}** not found! , Contact your Bruh .".format(member))

    @commands.command()
    async def inventory(self, ctx):
        """
        Lists items in your inventory.
        :param ctx:
        :return:
        """
        items = session.query(Inventory).filter_by(player_id=ctx.author.id).all()
        x = PrettyTable()
        x.field_names = ["Name", "Type", "Description", "Quantity"]
        if items is None:
            await ctx.send("No Items in your inventory, time to get to work!")
        else:
            for item in items:
                item_obj = session.query(Item).filter_by(id=item.item_id).first()
                x.add_row([item_obj.name, item_obj.types, item_obj.description, item.quantity])

            await ctx.send(emb(x))

    @commands.command()
    async def create(self, ctx, class_m):
        await create_player(ctx, class_m)

    @commands.command()
    async def market(self, ctx, number=20):
        """
        Buy and sell your goods in the market.
        """
        x = PrettyTable()
        x.field_names = ["Name", "Quantity", "Price"]
        test = Query(types='auction').get(number, 'id', 'desc')
        for item in test:
            x.add_row([item.item.name, item.quantity, item.price])
        await ctx.send("```Most Recent {} Listings: \n{}```".format(number, x))

    @commands.command()
    async def send(self, ctx, player=None, amount=None, message=None):
        """
        Send moolah to other players.
        """
        player = await search(ctx, player)

        if player is None:
            await ctx.send("Enter Player name to send Moolah. \n e.g ``` {}send billy 100 message[Optional]```".format(
                self.bot.master[ctx.guild.id]["prefix"][0]))

        elif amount is None:
            await ctx.send("Enter amount of Moolah to send!. \n e.g ``` {}send billy 100 message[Optional]```".format(
                self.bot.master[ctx.guild.id]["prefix"][0]))
        else:
            author = transaction(self.bot, ctx.author)
            reciever = transaction(self.bot, player)
            author.remove(amount)
            reciever.add(amount)
            await ctx.send("{} Moolah sent to {}!".format(amount, player))
            # DEBUG# await ctx.send("Sender Balance : {} Receiver Balance : {}".format(Query('user', ctx.author).get().moolah, Query('user', player).get().moolah))

    @commands.command()
    async def profession(self, ctx, number=None):
        """
        Select your profession or view profession.
        """
        prof_list = [None, "Miner", "Lumberjack", "Gatherer", "Smith", "Outfitter", "Chef"]
        Player = Character(ctx.author)
        if Player.has_chosen:
            await ctx.send(
                "You have already embarked on the jounery to become a master {} , there is not turing back!".format(Player.profession))

        elif number is None:
            await ctx.send(
                " __* **Gatherer Professions:** *__\n**[1] Miner**\n**[2] Lumberjack**\n**[3] Gatherer**\n__* **Crafting Professions** *__\n**[4] Smith**\n**[5] Outfitter**\n**[6] Chef**\n Choose Your Profession(1-6) , eg +profession 2 for Lumberjack")
        else:
            try:
                selection = int(number)
            except Exception as e:
                await ctx.send('Error enter a number for your profession !\n you went to the wrong selection exam..')
            selected_prof = prof_list[selection]

            try:
                Player = Query(types="player", obj=ctx.author).get()
                Player.profession = selected_prof
                session.commit()
                await ctx.send('You passed the selection exam ! You have selected {}, there is no turning back now !\n'.format(selected_prof))
            except Exception as e:
                await ctx.send('Error in selecting profession! You are paralyzed with indecision')

    @commands.command()
    async def topdog(self, ctx, selxp='moolah'):
        """
        Shows the Top 10 Holders of Moolah or Xp and your Position (Local or Global).
        """

        if selxp == 'moolah':
            selxp = True
        else:
            selxp = False

        x = PrettyTable()

        if selxp:
            x.field_names = ["Position", "Names", "Moolah"]
            test = Query(types='player').get(10, 'moolah', 'desc')
        else:
            x.field_names = ["Position", "Names", "Exp"]
            test = Query(types='player').get(10, 'exp', 'desc')
    
        lis_form = list(test)
        author = [x.id for x in lis_form]

        for item in test:
            if selxp:
                xp_selection = item.moolah
            else:
                xp_selection = item.exp

            user = self.bot.get_user(item.id)
            if ctx.author.id == item.id:
                name = "->>" + emoji_norm(ctx.author.name, "_") + "<<-"
            else:
                name = emoji_norm(user.name, "_")
            x.add_row([int(lis_form.index(item) + 1), name, xp_selection])

        if ctx.author.id not in author:
            if selxp:
                x.field_names = ["Position", "Names", "Moolah"]
                test1 = list(Query(types='player').get('all', 'moolah', 'desc'))
            else:
                x.field_names = ["Position", "Names", "Exp"]
                test1 = list(Query(types='player').get('all', 'exp', 'desc'))

            author = [test1.index(x) for x in test1 if x.id == ctx.author.id][0]
            mini_list = test1[author - 3:author + 3]
            x.add_row(["..........", "..........", ".........."])
            for member in mini_list:
                user = self.bot.get_user(member.id)
                if member.id == ctx.author.id:
                    x.add_row([int(author - 3 + mini_list.index(member)), "->>" + emoji_norm(user.name, "_") + "<<-",
                               member.exp])
                else:
                    x.add_row([int(author - 3 + mini_list.index(member)), user.name, member.exp])
        logo = ''' _____               _             
|_   _|             | |            
  | | ___  _ __   __| | ___   __ _ 
  | |/ _ \| '_ \ / _` |/ _ \ / _` |
  | | (_) | |_) | (_| | (_) | (_| |
  \_/\___/| .__/ \__,_|\___/ \__, |
          | |                 __/ |
          |_|                |___/ 

\n'''
        await ctx.send('```c\n{}{}```'.format(logo, x))

    @commands.command()
    async def role(self, ctx, action=None, role_name=None):
        """
        Lobby Moolah to increase your status.
        """
        test = Query(types='role').get(number='special', orderby='price', order='desc').filter_by(guild_id=ctx.guild.id)
        if action is None and role_name is None:
            x = PrettyTable()
            x.field_names = ["Name", "Price"]
            for item in test:
                if item.price is not None:
                    x.add_row([discord.utils.get(ctx.message.guild.roles, id=item.id).name, item.price])
            await ctx.send("```{}```".format(x))

        elif action == "buy" and role_name is not None:
            role = discord.utils.get(ctx.message.guild.roles, name=role_name)
            author = transaction(self.bot, ctx.author)
            is_sale = [x.price for x in test if x.id == role.id][0]
            if is_sale is None:
                await ctx.send("{} is not for sale on this server!.".format(role_name))
            else:
                author.remove(is_sale)
                await ctx.message.author.add_roles(role,
                                                   reason="Purchased Time:{}".format(datetime.now()))
                await ctx.send("Congrats you have purchased {}!.".format(role_name))
        elif action == "sell" and role_name is not None:
            await ctx.send("IN PROGRESS")

    async def VresourceDist(self):
        """
        Continuous function that distributes moolah to the miners
        :return:
        """
        await self.bot.wait_until_ready()
        logg.info("Resource distribution Started!")
        while True:
            await asyncio.sleep(60)
            for guild in self.bot.guilds:
                for channel in guild.voice_channels:
                    real_p = (x for x in channel.members if x.bot is False)
                    bots = (x for x in channel.members if x.bot is True)
                    if len(channel.members) > 1 and len(list(real_p)) > len(list(bots)):
                        for member in channel.members:
                            chara = Character(member)
                            if chara.has_chosen:
                                chara.exp += 1
                            else:
                                starter_pack = Item(id=70, name='Mysterious Package',
                                                    description='This package has never been opened , how exciting !',
                                                    base_value=0)
                                s_r = session.query(exists().where(
                                    Inventory.player_id == member.id and Inventory.item_id == starter_pack.id)).scalar()
                                if not s_r:
                                    inv_entry = Inventory(player_id=member.id, item_id=starter_pack.id, quantity=1)
                                    for item in [starter_pack, inv_entry]:
                                        try:
                                            session.add(item)
                                            session.commit()
                                        except Exception as e:
                                            session.rollback()
                                else:
                                    inv_object = session.query(Inventory).filter(
                                        Inventory.player_id == member.id).filter(
                                        Inventory.item_id == starter_pack.id).first()
                                    inv_object.quantity += 1
                                    session.commit()

    async def on_message(self, message):
        amount = 2
        pass


def setup(bot):
    bot.add_cog(Economy(bot))
