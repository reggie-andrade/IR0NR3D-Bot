# Import statements ===============================================================================================================

import discord
from discord.ext import commands
import re
import asyncio
import time
import csv
import pandas as pd

# Variables =======================================================================================================================

prefix = "-" # Variable for prefix, used everywhere when prefix is mentioned except comments.

client = discord.Client() # For connection to discord
bot = commands.Bot(command_prefix=prefix) # Sets prefix for bot

times = {} # Empty dictionary for user id's and the time thier battle ready ends. Used for checking if user is battle ready and calculating time remaining.
userTimers = {} # Empty dictionary for user id's and their corresponding timer object. Used for cancelling user's timers.

# Ranks dictionary to store basic Ironlights ranks. Can be changed with no issues.
ranks = {
    "b": "Bronze", 
    "s": "Silver", 
    "g": "Gold", 
    "p": "Platinum", 
    "d": "Diamond", 
    "e": "Elite", 
    "c": "Champion"
}

# Functions ======================================================================================================================

# Pretty loaded function to apply battle ready under a certain user. Timer has an upper limit of 24h due to restraints of the time module.
async def ApplyBattleReady(userid, duration, durationType, context, text):
    # Grabbing the battle ready role
    battleReady = discord.utils.get(context.author.guild.roles, name = "Battle Ready")

    embed=discord.Embed(title="Battle Ready applied", description=f"You're now battle ready for {text}! To cancel the duration, use the command **-ready cancel**.", color=discord.Color.green())

    # Function to start a timer which will grant battle ready for the duration.
    async def StartTimer(idnum, dur, durType):
        user = await context.author.guild.fetch_member(idnum)

        if durType == "h":
            # Grants role to user for set amount of time in hours
            await user.add_roles(battleReady) 
            await asyncio.sleep(dur * 3600)
            await user.remove_roles(battleReady)
            del times[idnum]
            del userTimers[idnum]
        elif durType == "m":
            # Grants role to user for set amount of time in minutes
            await user.add_roles(battleReady)
            await asyncio.sleep(duration * 60)
            await user.remove_roles(battleReady)
            del times[idnum]
            del userTimers[idnum]

    # Add user and end time to the "times" dictionary with proper duration based on duration type, and add user and timer object to the "userTimers" dictionary.
    if durationType == "h":
        times[userid] = time.time() + duration * 3600
        # Line of code to start a timer on different thread for the proper duration in the "userTimers" dictionary
        userTimers[userid] = asyncio.create_task(StartTimer(userid, duration, "h"))
    elif durationType == "m":
        times[userid] = time.time() + duration * 60
        userTimers[userid] = asyncio.create_task(StartTimer(userid, duration, "m"))

    await context.send(embed=embed)

# Basic function to grab the rank of any user from ranks.csv
def GetRank(userid):
    # Open file in read mode
    with open("ranks.csv", "r") as f:
        reader = csv.reader(f)
        rank = ""
        hasRank = False

        # Grab rank of given user using exception handling to handle non-integer strings
        for row in reader:
            try:
                if int(row[0]) == userid:
                    hasRank = True
                    rank = row[1]
            except:
                pass

        if hasRank:
            rankPrefix = rank[0].lower()
        else:
            rankPrefix = None

    return hasRank, rank, rankPrefix

# Events ==========================================================================================================================

# Simple event to print when bot is online
@bot.event
async def on_ready():
    print('IR0NR3D is online.')

# "Ready" command event with multiple sub-commands relating to the Battle Ready role
@bot.command()
async def ready(ctx, text):
    # Variables -----------------------------------------------------

    alreadyReady = False
    user = ctx.message.author.id

    # Loop which checks through the "times" dictionary to see if current user isn't already battle ready
    if len(times) != 0:
        for userid, endTime in times.items():
            if userid == user:
                alreadyReady = True
    
    # Commands -----------------------------------------------------

    # "-ready perm" command to permenantly give battle ready
    #----------------------------------------------------------------------------------
    if text == "perm":
        battleReady = discord.utils.get(ctx.author.guild.roles, name = "Battle Ready")
        
        # If user is already battle ready, send a message saying they're already ready.
        # Otherwise, grant the user the battle ready role until they remove it.
        if alreadyReady:
            embed=discord.Embed(description="You're already currently ready!", color=discord.Color.orange())
            await ctx.send(embed=embed)
        else:
            await ctx.message.author.add_roles(battleReady)

            # Add user to dictionaries under the times "0" which declare a permenant role
            times[user] = 0
            userTimers[user] = 0

            embed=discord.Embed(title="Battle Ready permenantly applied", description=f"You're now permenantly battle ready! To exit the role, use the command **-ready cancel**.\n\nNote: Make sure you remove the role once you're done, otherwise you'll keep getting pings!", color=discord.Color.gold())
            await ctx.send(embed=embed)


    # "-ready cancel" command to remove the battle ready role whether it was permenantly set or set for a duration
    #----------------------------------------------------------------------------------
    if text == "cancel":
        battleReady = discord.utils.get(ctx.author.guild.roles, name = "Battle Ready")

        # If user is already ready, remove their battle ready role and remove them from any other dictionaries. 
        # Otherwise, tell them they aren't ready.
        if alreadyReady:
            # If user isn't permenantly ready, cancel their timer
            if userTimers[user] != 0:
                userTimers[user].cancel()

            del times[user]
            del userTimers[user]
            await ctx.message.author.remove_roles(battleReady)

            embed=discord.Embed(title="Battle Ready removed", description="You've been unreadied. To ready up again, use the command **-ready** with the duration you'd like to be ready for (ex. -ready 2h, -ready 16m, -ready perm)", color=discord.Color.greyple())
            await ctx.send(embed=embed)          
        else:
            embed=discord.Embed(description="You aren't currently ready! To ready up, use the command **-ready** with the duration you'd like to be ready for (ex. -ready 2h, -ready 16m, -ready perm)", color=discord.Color.orange())
            await ctx.send(embed=embed)


    # "-ready list" command to list out the current users who are battle ready. Also allows for rank searching
    #----------------------------------------------------------------------------------
    if "list" in text:
        embedText = ""
        embed = discord.Embed(description="Empty", color=discord.Color.red())

        # Huge if statement to check if the user wants a normal list, or wants to search in the list
        if text == "list":
            # If times isn't empty, create and display list
            if len(times) != 0:
                for userid, endTime in times.items():
                    user = await ctx.author.guild.fetch_member(userid)
                    username = user.display_name
                    hasRank, rank, rankPrefix = GetRank(userid)

                    # Check if user time left is permenant or not, and format embed text
                    if endTime != 0:
                        timeRemaining = time.strftime("%H:%M:%S", time.gmtime(endTime - time.time()))

                        embedText = f"{embedText}\n{username} | Ready for {timeRemaining}"
                    else:
                        embedText = f"{embedText}\n{username} | Ready permanently"

                    if hasRank:
                        embedText = f"{embedText} | **{rank}**"

                embed=discord.Embed(title="Battle Ready list", description=embedText, color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(description="Nobody is currently battle ready :(", color=discord.Color.orange())
                await ctx.send(embed=embed)
        else:
            for ranking, fullRank in ranks.items():
                # If user wants to see only certain ranks in the list, create a rank-exclusive list and display
                if text == "list." + ranking:
                    if len(times) != 0:
                        for userid, endTime in times.items():
                            user = await ctx.author.guild.fetch_member(userid)
                            username = user.display_name
                            hasRank, rank, rankPrefix = GetRank(userid)

                            # Check if user matches rank search and is permanently ready or not
                            if hasRank and rankPrefix == ranking:
                                if endTime != 0:
                                    timeRemaining = time.strftime("%H:%M:%S", time.gmtime(endTime - time.time()))

                                    embedText = f"{embedText}\n{username} | Ready for {timeRemaining} | **{rank}**"
                                else:
                                    embedText = f"{embedText}\n{username} | Ready permanently | **{rank}**"

                        embed=discord.Embed(title=f"Battle Ready list ({ranks[ranking]})", description=embedText, color=discord.Color.blue())
                    if embedText == "":
                        embed=discord.Embed(description="Nobody in this rank is currently battle ready :(", color=discord.Color.orange())

            await ctx.send(embed=embed) # Send message variable


    # "-ready time" to show how much time a user has remaining until their battle ready expires
    #----------------------------------------------------------------------------------
    if text == "time":
        userFound = False
        
        # If user is ready, look for their end time in the list and display the remaining time.
        if alreadyReady:
            if times[user] != 0:
                timeRemaining = time.strftime("%H:%M:%S", time.gmtime(times[user] - time.time())) # Basic arithmatic to calculate duration remaining and formatting
                embed=discord.Embed(title="Duration remaining:", description=timeRemaining, color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title="Duration remaining:", description="Permanently ready", color=discord.Color.blue())
                await ctx.send(embed=embed)
        elif not alreadyReady or len(times) == 0:
            embed=discord.Embed(description=f"You aren't currently ready! To ready up, use the command **-ready** with the duration you'd like to be ready for (ex. -ready 2h, -ready 16m, -ready perm)", color=discord.Color.orange())
            await ctx.send(embed=embed)
    

    # "-ready [duration]" to give user the battle ready role for a set amount of time
    # This command isn't written effecienctly, and should be re-written in the future.
    #----------------------------------------------------------------------------------
    tempText = re.findall(r'\d+', text) # Temporary variable for splitting user input
    numberList = list(map(int, tempText)) # Takes all number values from the user's text and puts it in a list (ex. "2h3m" would return [2,3])

    # Exception handling in case "duration" is empty
    try:
        duration = numberList[0]
    except:
        duration = 0

    # Big chunk of if statements which essentially detect the format of the message and puts the user in battle ready if the format is correct.
    if text != "time" and "list" not in text and text != "cancel" and text != "perm":
        if not alreadyReady:
            if text == f"{duration}h" and duration <= 24:
                await ApplyBattleReady(user, duration, "h", ctx, text)
            elif text == f"{duration}m" and duration <= 59:
                await ApplyBattleReady(user, duration, "m", ctx, text)
            elif text == f"{duration}h" and duration > 24:
                embed=discord.Embed(description="Max duration for battle ready is 24h to preserve memory. To permanently ready up until you cancel, use the **-ready perm** command.", color=discord.Color.red())
                await ctx.send(embed=embed)
            elif text == f"{duration}m" and duration > 59:
                embed=discord.Embed(description=f"For hours, please use the hour format such as \"2h\".", color=discord.Color.red())
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(description=f"Invalid duration. Please use the proper format, such as \"2h\" or \"30m\".", color=discord.Color.red())
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(description="You're already currently ready!", color=discord.Color.orange())
            await ctx.send(embed=embed)

# "Rank" command using "ranks.csv" file to store user ranks and allows users to set their rank. Has multiple sub-commands.
@bot.command()
async def rank(ctx, text):
    # Variables -----------------------------------------------------

    user = ctx.message.author.id
    rankCSV = "ranks.csv"
    alreadyHasRank = False

    # Open block to check if user was already assigned a rank
    with open(rankCSV, "r") as f:
        reader = csv.reader(f)
        rowCount = 0
        rowFound = 0

        # For loop looking for user with exception handling to handle non-integer strings
        for row in reader:
            try:
                if int(row[0]) == user:
                    alreadyHasRank = True
                    rank = row[1]
                    rowFound = rowCount
            except:
                pass
                # Subtract from row count since non-integer string is the header
                rowCount -= 1

            rowCount += 1

    # Commands ----------------------------------------------------

    # "-rank view" for the invoker to view their rank
    #----------------------------------------------------------------------------------
    if text == "view":
        if alreadyHasRank:
            embed=discord.Embed(title="Currently set rank", description=f"Rank: **{rank}**", color=discord.Color.blue())
        else:
            embed=discord.Embed(description=f"You haven't set your rank! To set your rank, use the **-rank [abbreviation]** command to set your rank. (ex. \"-rank b\" for Bronze, \"-rank g\" for Gold,)", color=discord.Color.orange())

        await ctx.send(embed=embed)
    
    # "-rank del" to remove the invoker's rank if it has already been set
    #----------------------------------------------------------------------------------
    if text == "del":
        if alreadyHasRank:
            # Read the csv file using pandas, drop function to delete the row, and to_csv function to update the csv file
            rankfile = pd.read_csv(rankCSV)
            rankfile.drop(labels=rankfile.index[rowFound], axis=0, inplace=True)
            rankfile.to_csv("ranks.csv", index = False, header = True)

            embed=discord.Embed(title="Rank removed", description=f"Your rank has been removed from our database. To add your rank again, use the **-rank [abbreviation]** command to set your rank. (ex. \"-rank b\" for Bronze, \"-rank g\" for Gold,)", color=discord.Color.greyple())
        else:
            embed=discord.Embed(description=f"You haven't set your rank! To set your rank, use the **-rank [abbreviation]** command to set your rank. (ex. \"-rank b\" for Bronze, \"-rank g\" for Gold,)", color=discord.Color.orange())
            
        await ctx.send(embed=embed)


    # "-rank [abbreviation]" to set the invoker's rank to the inputted rank abbreviation
    #----------------------------------------------------------------------------------
    for rankPrefix, rankName in ranks.items():
        if text == rankPrefix:
            if alreadyHasRank:
                embed=discord.Embed(description="You've already set your rank! To change your rank, use the **-rank del** command to remove your rank, then set it again using this command.", color=discord.Color.orange())
            else:
                # Open block to write a new line to the csv file containing the invoker's rank
                with open(rankCSV, "a+", newline="") as f:
                    writer = csv.writer(f)
                    
                    writer.writerow([user, rankName])
                    embed=discord.Embed(title="Rank set", description="Your rank has been set! Your rank will appear next to your name in the battle ready list.\nNote: If you are reported to be using an invalid rank, your ability to use the rank command may be removed.", color=discord.Color.green())
            
            await ctx.send(embed=embed)

# Event to delete any text message sent in the #ironlights-art channel. Breaks if channel has no slowmode.
@bot.event
async def on_message(text):
    await bot.process_commands(text)
    if text.author.id != 967128726615752725 and len(text.attachments) == 0 and text.channel.id == 815980328988442684:
        art = bot.get_channel(815980328988442684)
        await art.purge(limit=1)
        await art.send("Please keep this channel clear of text chats!")
        await asyncio.sleep(5)
        await art.purge(limit=1)
    elif len(text.attachments) > 0 and text.channel.id == 815980328988442684:
        await text.add_reaction("⭐")

# Finalization ======================================================================================================================
# Run the bot using the bot's key
bot.run('') 
