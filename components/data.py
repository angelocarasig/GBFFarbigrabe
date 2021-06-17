﻿import discord
import asyncio
import threading
import json
import time
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# Save Component
# ----------------------------------------------------------------------------------------------------------------
# This component manages the save data file (save.json)
# It also lets you load config.json (once at startup)
# Works in tandem with the Drive component
# ----------------------------------------------------------------------------------------------------------------

class Data():
    def __init__(self, bot):
        self.bot = bot
        self.bot.drive = None
        self.config = {}
        self.save = {}
        self.saveversion = 1
        self.pending = False
        self.autosaving = False
        self.lock = threading.Lock()
        
        self.errn = 0 # to change

    def init(self):
        pass

    def loadConfig(self): # pretty simple, load the config file. should only be used once at the start
        try:
            with open('config.json') as f:
                data = json.load(f, object_pairs_hook=self.bot.util.json_deserial_dict) # deserializer here
                self.config = data
            return True
        except Exception as e:
            print('loadConfig(): {}\nCheck your \'config.json\' for the above error.'.format(self.bot.util.pexc(e)))
            return False

    def loadData(self): # same thing but for save.json
        try:
            with open('save.json') as f:
                data = json.load(f, object_pairs_hook=self.bot.util.json_deserial_dict) # deserializer here
                ver = data.get('version', None)
                if ver is None:
                    raise Exception("This save file isn't compatible")
                elif ver < self.saveversion:
                    if ver == 0:
                        for id in data['reminders']:
                            for r in data['reminders'][id]:
                                if len(r) == 2:
                                    r.append("")
                        try: data['gbfdata'].pop('new_ticket')
                        except: pass
                        try: data['gbfdata'].pop('count')
                        except: pass
                    data['version'] = self.saveversion
                elif ver > self.saveversion:
                    raise Exception("Save file version higher than the expected version")
                with self.lock:
                    self.save = self.checkData(data)
                    self.pending = False
                return True
        except Exception as e:
            self.errn += 1
            print('load(): {}'.format(self.bot.util.pexc(e)))
            return False

    def saveData(self): # saving (lock isn't used, use it outside!)
        try:
            with open('save.json', 'w') as outfile:
                json.dump(self.save, outfile, default=self.bot.util.json_serial) # locally first
                if not self.bot.drive.save(json.dumps(self.save, default=self.bot.util.json_serial)): # sending to the google drive
                    raise Exception("Couldn't save to google drive")
            return True
        except Exception as e:
            self.errn += 1
            print('save(): {}'.format(self.bot.util.pexc(e)))
            return False

    def checkData(self, data): # used to initialize missing data or remove useless data from the save file
        expected = {
            'version':self.saveversion,
            'guilds': {'banned':[], 'owners':[], 'pending':{}},
            'prefixes': {},
            'gbfaccounts': [],
            'gbfcurrent': 0,
            'gbfversion': None,
            'gbfdata': {},
            'bot_maintenance': None,
            'maintenance': {"state" : False, "time" : None, "duration" : 0},
            'stream': {'time':None, 'content':[]},
            'schedule': [],
            'st': {},
            'spark': [{}, []],
            'gw': {'state':False},
            'valiant': {'state':False},
            'reminders': {},
            'permitted': {},
            'news': {},
            'extra': {},
            'gbfids': {},
            'assignablerole': {},
            'youtracker': None
        }
        for k in list(data.keys()): # remove useless
            if k not in expected:
                data.pop(k)
        for k in expected: # add missing
            if k not in data:
                data[k] = expected[k]
        return data

    async def autosave(self, discordDump = False): # called when pending is true by statustask()
        if self.autosaving: return
        self.autosaving = True
        result = False
        for i in range(0, 3): # try a few times
            with self.lock:
                if self.saveData():
                    self.pending = False
                    result = True
                    break
            await asyncio.sleep(0.001)
        if not result:
            await self.bot.send('debug', embed=self.bot.util.embed(title="Failed Save", timestamp=self.bot.util.timestamp()))
            discordDump = True
        if discordDump:
            try:
                with open('save.json', 'r') as infile:
                    df = discord.File(infile)
                    await self.bot.send('debug', 'save.json', file=df)
                    df.close()
            except:
                pass
        self.autosaving = False

    def clean_spark(self): # clean up spark data
        count = 0
        c = datetime.utcnow()
        keys = list(self.bot.data.save['spark'][0].keys())
        for id in keys:
            if len(self.bot.data.save['spark'][0][id]) == 3: # backward compatibility
                with self.bot.data.lock:
                    self.bot.data.save['spark'][0][id].append(c)
                    self.bot.data.pending = True
            else:
                d = c - self.bot.data.save['spark'][0][id][3]
                if d.days >= 30:
                    with self.bot.data.lock:
                        del self.bot.data.save['spark'][0][id]
                        self.bot.data.pending = True
                    count += 1
        return count

    def clean_profile(self): # clean up profiles
        count = 0
        keys = list(self.bot.data.save['gbfids'].keys())
        for uid in keys:
            found = False
            for g in self.bot.guilds:
                 if g.get_member(int(uid)) is not None:
                    found = True
                    break
            if not found:
                count += 1
                with self.bot.data.lock:
                    self.bot.data.save['gbfids'].pop(uid)
                    self.bot.data.pending = True
        return count

    def clean_schedule(self): # clean up schedule
        c = self.bot.util.JST()
        fd = c.replace(day=1, hour=12, minute=15, second=0, microsecond=0) # day of the next schedule drop, 15min after
        if fd < c:
            if fd.month == 12: fd = fd.replace(year=fd.year+1, month=1)
            else: fd = fd.replace(month=fd.month+1)
        d = fd - c
        new_schedule = []
        if self.bot.twitter.api is not None and d.days < 1: # retrieve schedule from @granblue_en if we are close to the date
            time.sleep(d.seconds) # wait until koregra to try to get the schedule
            tw = self.bot.twitter.timeline('granblue_en')
            if tw is not None:
                for t in tw:
                    txt = t.full_text
                    if txt.find(" = ") != -1 and txt.find("chedule\n") != -1:
                        try:
                            s = txt.find("https://t.co/")
                            if s != -1: txt = txt[:s]
                            txt = txt.replace('\n\n', '\n')
                            txt = txt[txt.find("chedule\n")+len("chedule\n"):]
                            new_schedule = txt.replace('\n', ' = ').split(' = ')
                            while len(new_schedule) > 0 and new_schedule[0] == '': new_schedule.pop(0)
                        except: pass
                        break
        else: # else, just clean up old entries
            for i in range(0, ((len(self.bot.data.save['schedule'])//2)*2), 2):
                try:
                    date = self.bot.data.save['schedule'][i].replace(" ", "").split("-")[-1].split("/")
                    x = c.replace(month=int(date[0]), day=int(date[1])+1, microsecond=0)
                    if c - x > timedelta(days=160):
                        x = x.replace(year=x.year+1)
                    if c >= x:
                        continue
                except:
                    pass
                new_schedule.append(self.bot.data.save['schedule'][i])
                new_schedule.append(self.bot.data.save['schedule'][i+1])
        if len(new_schedule) != 0 and len(new_schedule) != len(self.bot.data.save['schedule']):
            with self.bot.data.lock:
                self.bot.data.save['schedule'] = new_schedule
                self.bot.data.pending = True
            return True
        return False