from datetime import datetime
import os
import discord
from discord.ext import commands
import re

# Fetch python bot token
from dotenv import load_dotenv
from os import getenv
load_dotenv('token.env')
token = getenv("TOKEN")

from csvreader import CsvReader
from player import Player
from scorecard import Scorecard
from scorecards import Scorecards

# discord client
bot = commands.Bot(command_prefix='%')

def is_path_empty(path):
    if os.path.exists(path) and not os.path.isfile(path):  
        if not os.listdir(path):
            # Empty directory
            return True
        else:
            # Not empty directory
            return False
    else:
        # The path is either for a file or not valid
        return True

def get_scorecards(path):
    scorecards = Scorecards()
    for file in os.listdir(path):
        if file.endswith(".csv"):
            csvreader = CsvReader(path, file)
            scorecard = csvreader.parse()

            scorecards.add_scorecard(scorecard)

    return scorecards

def get_scorecards_course(path, course):
    scorecards = Scorecards()
    for file in os.listdir(path):
        if file.endswith(".csv"):
            csvreader = CsvReader(path, file)
            scorecard = csvreader.parse_course(course)
            if scorecard is not None:
                scorecards.add_scorecard(scorecard)

    return scorecards

def get_scorecards_date(path, date, date_to = ''):
    scorecards = Scorecards()
    for file in os.listdir(path):
        if file.endswith(".csv"):
            csvreader = CsvReader(path, file)
            scorecard = csvreader.parse_dates(date, date_to)            

            if scorecard is not None:
                scorecards.add_scorecard(scorecard)

    return scorecards

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user} - {discord.__version__}')
    await bot.change_presence(activity=discord.Game(name="Disc golf"))

@bot.event
async def on_message(message):
    path = str(f'{message.guild.name}\{message.channel}')
    
    # any attachments in the message?
    if message.attachments:
        for attachment in message.attachments:
            if 'text/csv' in attachment.content_type:
                if not os.path.exists(path):
                    os.makedirs(path)
                await attachment.save(fp=f"{path}\{attachment.filename}") # saves the file in a server/channel folder
                print(f'csv attached and stored in {path}\{attachment.filename}!')
                
                csvreader = CsvReader(path, attachment.filename)
                scorecard = csvreader.parse()
                
                await message.channel.send(embed=scorecard.get_embed(message.author.avatar_url))
                await message.delete()
                return
    elif message.guild.id == 597085958244139022:
        def findWholeWord(w):
            return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search
        
        disc_golf_words = ['disc', 'disc-golf', 'discgolf']
        for word in disc_golf_words:
            if findWholeWord(word)(message.content.lower()) is not None:
                emoji = '<a:shutupandtakemymoney:751168620339527830>'
                await message.add_reaction(emoji)
                break 
        
        if 'bomb' in message.content.lower():
            emoji = '💣'
            await message.add_reaction(emoji)
    
    await bot.process_commands(message)

@bot.command()
async def files(ctx):
    path = str(f'{ctx.guild.name}\{ctx.channel}')

    if is_path_empty(path):
        await ctx.send('No files stored for this channel')
        return
        
    msg_to_send = ''
    file_count = 0
    for file in os.listdir(path):
        if file.endswith(".csv"):
            file_count += 1
            print(os.path.join(f'{path}\{file}'))
            msg_to_send += f'\n{file}'
    
    if file_count:     
        await ctx.send(f'No of files: {file_count}\n{msg_to_send}')
    else:
        await ctx.send('No .csv files stored for this channel')

@bot.command()
async def dates(ctx):

    path = str(f'{ctx.guild.name}\{ctx.channel}')

    if is_path_empty(path):
        await ctx.send("No scores stored for this channel")
        return
    
    # Get current dates
    datelist = []
    for file in os.listdir(path):
        if file.endswith(".csv"):
            csvreader = CsvReader(path, file)
            scorecard = csvreader.parse()

            date = scorecard.date_time.date()

            if date not in datelist:
                datelist.append(date)
    
    msg = ''
    for date in datelist:
        msg += f'\n{date}'

    await ctx.send(msg)

@bot.command()
async def scores(ctx, *args):  
    path = str(f'{ctx.guild.name}\{ctx.channel}')

    # Check current scores stored in this channel
    if is_path_empty(path):
        await ctx.send('No scores stored for this channel')
        return

    if args:
        print(f'%scores: {len(args)} arguments:', ', '.join(args))

        if args[0] == "course":
            if len(args) < 2:
                ctx.send("Missing coursename")
                return

            scorecards = get_scorecards_course(path, args[1])           

            if (scorecards.scorecardlist):               
                await ctx.send(embed=scorecards.get_embed(ctx.author.avatar_url)) 
            else:
                await ctx.send("No courses found")

        if args[0] == "date":
            if len(args) < 2:
                ctx.send("Missing date")
                return
            
            date = ''                
            try:
                date = datetime.strptime(args[1],'%d.%m.%Y')    
            except ValueError:
                await ctx.send("Invalid format in date 1 - should be 01.12.2021")
                return

            if len(args) == 2:
                scorecards = get_scorecards_date(path, date)
            if (len(args) > 2):
                date_to = ''
                try:
                    date_to = datetime.strptime(args[2],'%d.%m.%Y')    
                except ValueError:
                    await ctx.send("Invalid format in date 2 - should be 01.12.2021")
                    return

                scorecards = get_scorecards_date(path, date, date_to)                                 

            if (scorecards.scorecardlist):               
                await ctx.send(embed=scorecards.get_embed(ctx.author.avatar_url)) 
            else:
                await ctx.send("No courses found")
            
    else: # no args, list all scores
        scorecards = get_scorecards(path)

        if (scorecards.scorecardlist):               
            await ctx.send(embed=scorecards.get_embed(ctx.author.avatar_url))  
        else:
            await ctx.send("No courses found")
      
bot.run(token)
