﻿import disnake
from disnake.ext import commands
import asyncio
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# Reminder Cog
# ----------------------------------------------------------------------------------------------------------------
# Let users setup and manage "reminders" for later
# ----------------------------------------------------------------------------------------------------------------

class Reminder(commands.Cog):
    """Set Reminders."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5e17e3

    def startTasks(self):
        self.bot.runTask('reminder', self.remindertask)

    """checkReminders()
    Check the reminders ready to send.
    Update the save datas if the reminders are set in the old format.
    
    Returns
    --------
    dict: Reminders to send
    """
    def checkReminders(self):
        try:
            send = {}
            c = self.bot.util.JST() + timedelta(seconds=30)
            keys = list(self.bot.data.save['reminders'].keys())
            for r in keys:
                di = 0
                while di < len(self.bot.data.save['reminders'][r]):
                    if c > self.bot.data.save['reminders'][r][di][0]:
                        if r not in send: send[r] = []
                        with self.bot.data.lock:
                            send[r].append(self.bot.data.save['reminders'][r][di][1][:1900])
                            self.bot.data.save['reminders'][r].pop(di)
                            self.bot.data.pending = True
                    else:
                        di += 1
                if len(self.bot.data.save['reminders'][r]) == 0:
                    with self.bot.data.lock:
                        self.bot.data.save['reminders'].pop(r)
                        self.bot.data.pending = True
            return send
        except:
            return {}

    """remindertask()
    Bot Task managing the reminders set by the users
    """
    async def remindertask(self):
        while True:
            if not self.bot.running: return
            try:
                messages = await self.bot.do(self.checkReminders)
                for id in messages:
                    u = self.bot.get_or_fetch_user(int(id))
                    for m in messages[id]:
                        try:
                            await u.send(embed=self.bot.util.embed(title="Reminder", description=m))
                        except Exception as e:
                            await self.bot.sendError('remindertask', "User: {}\nReminder: {}\nError: {}".format(u.name, m, self.bot.util.pexc(e)))
                            break
            except asyncio.CancelledError:
                await self.bot.sendError('remindertask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('remindertask', e)
                await asyncio.sleep(200)
            await asyncio.sleep(40)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def remind(self, inter, duration : str = commands.Param(description="Format: XdXhXmXs"), msg : str = commands.Param(description="Content of the reminder")):
        """Remind you of something at the specified time (±30 seconds precision)"""
        id = str(inter.author.id)
        if id not in self.bot.data.save['reminders']:
            self.bot.data.save['reminders'][id] = []
        if len(self.bot.data.save['reminders'][id]) >= 5 and inter.author.id != self.bot.owner.id:
            await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", description="Sorry, I'm limited to 5 reminders per user 🙇", color=self.color), ephemeral=True)
            return
        try:
            d = self.bot.util.str2delta(duration)
            if d is None: raise Exception()
        except:
            await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", description="Invalid duration string `{}`, format is `NdNhNm`".format(duration), color=self.color), ephemeral=True)
            return
        if msg == "":
            await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", description="Tell me what I'm supposed to remind you 🤔", color=self.color), ephemeral=True)
            return
        if len(msg) > 200:
            await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", description="Reminders are limited to 200 characters", color=self.color), ephemeral=True)
            return
        try:
            with self.bot.data.lock:
                self.bot.data.save['reminders'][id].append([datetime.utcnow().replace(microsecond=0) + timedelta(seconds=32400) + d, msg]) # keep JST
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        except:
            await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", footer="I have no clues about what went wrong", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def remindlist(self, inter):
        """Post your current list of reminders"""
        id = str(inter.author.id)
        if id not in self.bot.data.save['reminders'] or len(self.bot.data.save['reminders'][id]) == 0:
            await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", description="You don't have any reminders", color=self.color), ephemeral=True)
        else:
            embed = disnake.Embed(title="{}'s Reminder List".format(inter.author.display_name), color=self.color)
            embed.set_thumbnail(url=inter.author.display_avatar)
            for i in range(0, len(self.bot.data.save['reminders'][id])):
                embed.add_field(name="#{} ▫️ {:%Y/%m/%d %H:%M} JST".format(i, self.bot.data.save['reminders'][id][i][0]), value=self.bot.data.save['reminders'][id][i][1], inline=False)
            await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reminddel(self, inter, rid : int = commands.Param(description="Number of the reminder to delete")):
        """Delete one of your reminders"""
        id = str(inter.author.id)
        if id not in self.bot.data.save['reminders'] or len(self.bot.data.save['reminders'][id]) == 0:
            await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", description="You don't have any reminders", color=self.color), ephemeral=True)
        else:
            if rid < 0 or rid >= len(self.bot.data.save['reminders'][id]):
                await inter.response.send_message(embed=self.bot.util.embed(title="Reminder Error", description="Invalid id `{}`".format(rid), color=self.color), ephemeral=True)
            else:
                with self.bot.data.lock:
                    self.bot.data.save['reminders'][id].pop(rid)
                    if len(self.bot.data.save['reminders'][id]) == 0:
                        self.bot.data.save['reminders'].pop(id)
                    self.bot.data.pending = True
                await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)