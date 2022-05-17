# Import statements ===============================================================================================================

from pickle import FALSE
import discord
from discord.ext import commands
import re
import asyncio
import time
import csv

# Variables =======================================================================================================================

prefix = "-" # Variable for prefix, used everywhere when prefix is mentioned except comments

client = discord.Client() # For connection to discord
bot = commands.Bot(command_prefix=prefix) # Sets prefix for bot

times = {} # Empty dictionary for user id's and the time thier battle ready ends. Used for checking if user is battle ready and calculating time remaining.
userTimers = {} # Empty dictionary for user id's and their corresponding timer object. Used for cancelling user's timers

ranks = {
    "b1": "Bronze I", 
    "b2": "Bronze II", 
    "b3": "Bronze III", 
    "s1": "Silver I", 
    "s2": "Silver II", 
    "s3": "Silver III", 
    "g1": "Gold I", 
    "g2": "Gold II", 
    "g3": "Gold III", 
    "p1": "Platinum I", 
    "p2": "Platinum II", 
    "p3": "Platinum III", 
    "d1": "Diamond I", 
    "d2": "Diamond II", 
    "d3": "Diamond III", 
    "e": "Elite", 
    "c": "Champion"
}

# Functions ======================================================================================================================

# Pretty loaded function to apply battle ready under a certain user. Timer has an upper limit of 24h due to restraints of the time module.
async def ApplyBattleReady(userid, duration, durationType, context, text):
    # Grabbing the battle ready role
    battleReady = discord.utils.get(context.author.guild.roles, name = "Battle Ready")

    # Declaring the embed to send
    embed=discord.Embed(title="Battle Ready applied", description=f"You're now battle ready for {text}! To cancel the duration, use the command **-ready cancel**.", color=discord.Color.green())

    # Function to start a timer which will grant battle ready for the duration.
    async def StartTimer(idnum, dur, durType):
        # Get user object of the user to start the timer under
        user = await context.author.guild.fetch_member(idnum)

        # Detect if duration is hours or minutes
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
        userTimers[userid] = asyncio.create_task(StartTimer(userid, duration, "h")) # Line of code to start a timer for the proper duration in the "userTimers" dictionary
    elif durationType == "m":
        times[userid] = time.time() + duration * 60
        userTimers[userid] = asyncio.create_task(StartTimer(userid, duration, "m")) # Line of code to start a timer for the proper duration in the "userTimers" dictionary

    # Send embed message saying the user is now ready
    await context.send(embed=embed)

def GetRank(userid):
    with open("ranks.csv", "r") as f:
        reader = csv.reader(f)
        rank = ""
        hasRank = False

        for row in reader:
            if int(row[0]) == userid:
                hasRank = True
                rank = row[1]
    return hasRank, rank

# Events ==========================================================================================================================

# Simple event to print when bot is online
@bot.event
async def on_ready():
    print('IR0NR3D is online.')

# "Ready" command event with multiple sub-commands relating to the Battle Ready role
@bot.command()
async def ready(ctx, text):
    # Variables -----------------------------------------------------

    alreadyReady = False # alreadyReady variable which defaults to "False"
    user = ctx.message.author.id # Assignes "user" the id of invoking user

    # Loop which checks through the "times" dictionary to see if current user isn't already battle ready
    if len(times) != 0:
        for userid, endTime in times.items():
            if userid == user:
                alreadyReady = True
    
    # Commands -----------------------------------------------------

    # "-ready perm" command to permenantly give battle ready
    #----------------------------------------------------------------------------------
    if text == "perm":
        # Grab the battle ready role
        battleReady = discord.utils.get(ctx.author.guild.roles, name = "Battle Ready")
        
        # If user is already battle ready, send a message saying they're already ready.
        # Otherwise, grant the user the battle ready role until they remove it.
        if alreadyReady:
            embed=discord.Embed(description="You're already currently ready!", color=discord.Color.orange())
            await ctx.send(embed=embed)
        else:
            # Grant the battle ready role
            await ctx.message.author.add_roles(battleReady)

            # Add user to dictionaries under the times "0" which declare a permenant role
            times[user] = 0
            userTimers[user] = 0

            # Send message saying battle ready is permenantly applied
            embed=discord.Embed(title="Battle Ready permenantly applied", description=f"You're now permenantly battle ready! To exit the role, use the command **-ready cancel**.\n\nNote: Make sure you remove the role once you're done, otherwise you'll keep getting pings!", color=discord.Color.gold())
            await ctx.send(embed=embed)


    # "-ready cancel" command to remove the battle ready role whether it was permenantly set or set for a duration
    #----------------------------------------------------------------------------------
    if text == "cancel":
        # Grab the battle ready role
        battleReady = discord.utils.get(ctx.author.guild.roles, name = "Battle Ready")

        # If user is already ready, remove their battle ready role and remove them from any other dictionaries. 
        # Otherwise, tell them they aren't ready.
        if alreadyReady:
            # If user isn't permenantly ready, cancel their timer
            if userTimers[user] != 0:
                userTimers[user].cancel()

            # Remove user from times dictionary and userTimers dictionary
            del times[user]
            del userTimers[user]

            # Remove user from battle ready role
            await ctx.message.author.remove_roles(battleReady)

            # Send message saying the user's battle ready has been removed
            embed=discord.Embed(title="Battle Ready removed", description="You've been unreadied. To ready up again, use the command **-ready** with the duration you'd like to be ready for (ex. -ready 2h, -ready 16m, -ready perm)", color=discord.Color.greyple())
            await ctx.send(embed=embed)          
        else:
            # Send message saying the user isn't currently ready
            embed=discord.Embed(description="You aren't currently ready! To ready up, use the command **-ready** with the duration you'd like to be ready for (ex. -ready 2h, -ready 16m, -ready perm)", color=discord.Color.orange())
            await ctx.send(embed=embed)


    # "-ready list" command to list out the current users who are battle ready
    #----------------------------------------------------------------------------------
    if text == "list":
        embedText = "" # Empty message variable to store end message

        # Check if dictionary isn't empty
        if len(times) != 0:
            # Loop through dictionary and display user's display name along with the time they have remaining on battle ready.
            for userid, endTime in times.items():
                # Get user object, and get username from object
                user = await ctx.author.guild.fetch_member(userid)
                username = user.display_name

                # Get if user has a valid rank and the rank they have using the GetRank function
                hasRank, rank = GetRank(userid)

                # Check if user time left is permenant or not, and format embed text
                if endTime != 0:
                    timeRemaining = time.strftime("%H:%M:%S", time.gmtime(endTime - time.time()))

                    embedText = f"{embedText}\n{username} | Ready for {timeRemaining}"
                else:
                    embedText = f"{embedText}\n{username} | Ready permanently"

                # Check if user has rank, and format embed text
                if hasRank:
                    embedText = f"{embedText} | **{rank}**"

            # Set message
            embed=discord.Embed(title="Battle Ready list", description=embedText, color=discord.Color.blue())
        else:
            # If dictionary is empty, set message to this.
            embed=discord.Embed(description="Nobody is currently battle ready :(", color=discord.Color.orange())

        await ctx.send(embed=embed) # Send message variable


    # "-ready time" to show how much time a user has remaining until their battle ready expires
    #----------------------------------------------------------------------------------
    if text == "time":
        userFound = False
        for userid, endTime in times.items():
            if userid == user:
                userFound = True
                if endTime != 0:
                    timeRemaining = time.strftime("%H:%M:%S", time.gmtime(times[user] - time.time()))
                    embed=discord.Embed(title="Duration remaining:", description=timeRemaining, color=discord.Color.blue())
                    await ctx.send(embed=embed)
                else:
                    embed=discord.Embed(title="Duration remaining:", description="Permanently ready", color=discord.Color.blue())
                    await ctx.send(embed=embed)
        if not userFound:
            embed=discord.Embed(description=f"You aren't currently ready! To ready up, use the command **-ready** with the duration you'd like to be ready for (ex. -ready 2h, -ready 16m, -ready perm)", color=discord.Color.orange())
            await ctx.send(embed=embed)
        if len(times) == 0:
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

    # Big chunk of if statements which essentially detect the format of the message and puts the user in battle ready if the format is correct. Only runs if the user is not ready.
    if text != "time" and text != "list" and text != "cancel" and text != "perm":
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

# "Rank" command using "ranks.csv" file to store user ranks and allows users to set their rank.
@bot.command()
async def rank(ctx, text):
    user = ctx.message.author.id
    alreadyHasRank = False

    with open("ranks.csv", "r") as f:
        reader = csv.reader(f)

        for row in reader:
            if int(row[0]) == user:
                alreadyHasRank = True
                rank = row[1]

    if text == "view":
        if alreadyHasRank:
            embed=discord.Embed(title="Currently set rank", description=f"Rank: **{rank}**", color=discord.Color.blue())
        else:
            embed=discord.Embed(description=f"You haven't set your rank! To set your rank, use the **-rank [abbreviation]** to set your rank. (ex. -rank b2, -rank g1, -rank c)", color=discord.Color.orange())

        await ctx.send(embed=embed)

    for rank, rankName in ranks.items():
        if text == rank:
            if alreadyHasRank:
                embed=discord.Embed(description="You've already set your rank! To change your rank, use the **-rank del** command to remove your rank, then set it again using this command.", color=discord.Color.orange())
            else:
                with open("ranks.csv", "a+", newline="") as f:
                    writer = csv.writer(f)
                    
                    writer.writerow([user, rankName])
                    embed=discord.Embed(title="Rank set", description="Your rank has been set! Your rank will appear next to your name in the battle ready list.\nNote: If you are reported to be using an invalid rank, your ability to use the rank command may be removed.", color=discord.Color.green())
            
            await ctx.send(embed=embed)

# Finalization ======================================================================================================================
# Run the bot using the bot's key
bot.run('OTY3MTI4NzI2NjE1NzUyNzI1.Gdsl-v.i2SsxGmWmG3dmj1rMvTAWVcc6eHAwzdcsMFYAw') 
