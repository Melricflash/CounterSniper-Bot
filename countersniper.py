import discord
import os
from discord.ext import commands
from discord.utils import get
import csv
import pandas as pd

import traceback

# Live Activity for bot
#activityName = discord.Activity(type=discord.ActivityType.watching, name="Khoslaa | Message melricflash for support")
activityName = discord.CustomActivity(name="Message @melricflash for support")

bot = commands.Bot(command_prefix="?", intents = discord.Intents.all(), activity=activityName)

# Change for prod server
fnRoleID = 1322316783805268008

'''
Classes
'''
class EGSModal(discord.ui.Modal, title="FN Customs Application"):
    egsForm = discord.ui.TextInput(
        label='Enter EGS Username',
        placeholder='Epic Games Username...'
    )

    # To retrieve the information from the form, we handle it in this function
    async def on_submit(self, interaction: discord.Interaction):

        # Retrieve submitted EGS username and Discord Username
        egsUsername = self.egsForm.value
        discordUsername = interaction.user.name
        discordID = interaction.user.id

        print(f"Data received from {discordUsername}: {egsUsername}")

        # Check if a blacklist database exists, then check if the user is already on the blacklist
        if os.path.exists('blacklist.csv'):
            if checkBlacklist(discordUsername, egsUsername, 'blacklist.csv'):
                await interaction.response.send_message(f"You have been blacklisted for breaking the Khoslaa FN Customs Terms and Conditions, lmao go cry to a mod", ephemeral=True)
                return

        # Next we want to pass to a function that will store this in a database if name doesnt exist
        DBstatus = saveToDB(discordUsername, discordID, egsUsername, 'discordEgs.csv')

        if DBstatus == 1:
            await interaction.response.send_message(f'An application was already submitted for either Discord: {discordUsername} or EGS: {egsUsername}', ephemeral=True)
            return
        
        await interaction.response.send_message(f'Your application was submitted!', ephemeral=True)

        # If checks pass, we add the role to the user
        guild = interaction.guild
        member = interaction.user

        # Add role to the user using the role ID
        role = guild.get_role(fnRoleID)
        await member.add_roles(role)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Something went wrong!', ephemeral=True)

        traceback.print_exception(type(error), error, error.__traceback__)


class EGSButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Start Application", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        modal = EGSModal()
        await interaction.response.send_modal(modal)


class EGSView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(EGSButton())


'''
Functions
'''

# Function to store a Discord Name and EGS Name in a CSV file | Blacklisting
def saveToDB(discName, discID, EGSName, fileName):

    filename = fileName
    data = {'DiscordUsername': [discName], 'DiscordID': [discID], 'EGSUsername': [EGSName]}

    # Create a new file if it doesnt exist
    if not os.path.exists(filename):
        df = pd.DataFrame(data)
        df.to_csv(filename, index = False)

    else:
        df = pd.read_csv(filename)
        
        # Check if an entry exists
        if df['DiscordUsername'].isin([discName]).any() or df['DiscordID'].isin([discID]).any() or df['EGSUsername'].isin([EGSName]).any():
            print(f"An application was already submitted for either Discord: {discName} or EGS: {EGSName}")
            return 1

        # Update the database
        else:
            tempFrame = pd.DataFrame(data)
            df = pd.concat([df, tempFrame], ignore_index=True)

            df.to_csv(filename, index=False)

# Function to find a discord username using their registered EGS name 
def findDiscordFromDB(EGSName):
    filename = 'discordEgs.csv'

    # Put the CSV into pandas dataframe
    df = pd.read_csv(filename)

    # Filter to get discord from egs name
    result = df.loc[df['EGSUsername'] == EGSName, 'DiscordUsername']

    resultID = df.loc[df['EGSUsername'] == EGSName, 'DiscordID']
    
    # Check if a user was found
    if not result.empty:
        print(result.iloc[0])
        # Return just the discord username for later use
        # return result.iloc[0]
    else:
        print("EGS User not found in DB")
        return 0, 0
    
    # Check if user id was found
    if not resultID.empty:
        print(resultID.iloc[0])
    else:
        print("EGS User could not be tied to a Discord ID")
        return 0, 0

    return result.iloc[0], resultID.iloc[0]

# Function to check if an given account is in the blacklist database (note to self, could make this more modular for later functions?)
def checkBlacklist(discName, EGSName, filename):
    df = pd.read_csv(filename)

    # Check if the discord username or EGS username exists in the blacklist
    if df['DiscordUsername'].isin([discName]).any() or df['EGSUsername'].isin([EGSName]).any():
        return True
    else:
        return False

'''
Async Functions
'''


@bot.tree.command(name = "test_egs_modal", description="Requests EGS Form")
async def create_EGS_Message(interaction: discord.Interaction):
    view = EGSView()
    await interaction.response.send_message("To Join Fortnite Custom Games, you must provide your Epic Games Account Username, **exactly as it's spelt as you cannot change this later**.\nPress the button below to do this:\n", view=view)

@bot.tree.command(name = "test_add_to_blacklist", description="Add a user to the blacklist via Epic Games Username")
async def add_to_blacklist(interaction: discord.Interaction, egs_username: str):
    
    # Check for the discord user in the main DB
    discUser, discID = findDiscordFromDB(egs_username)
    
    # If a discord username was not found for the EGS name, send error
    if discUser == 0 or discID == 0:
        await interaction.response.send_message("A matching Discord username was not found in the DB for this EGS name...", ephemeral=True)
        return

    # Get the member object by searching via name
    guild = interaction.guild

    # Get member via username
    #member = discord.utils.find(lambda m: m.name == discUser, guild.members)

    # Get member via discordID, allows for changing username
    member = guild.get_member(discID)


    # If member is not in the server, send message
    if not member:
        await interaction.response.send_message(f"Discord member: {discUser} is apparently not in the server...", ephemeral=True)

    # Remove role from member object
    role = guild.get_role(fnRoleID)
    await member.remove_roles(role)

    # Add user to the blacklist DB
    saveToDB(discUser, discID, egs_username, "blacklist.csv")

    print(f"Role removed from {discUser} and added to blacklist!")
    
    # Send success message
    await interaction.response.send_message(f"Added {discUser} to the blacklist and removed their role.", ephemeral=True)

# Function to create a message when reacted to will open a form to fill in EGS account info (not in use)
@bot.tree.command(name = "test_egsrolemessage", description="Sends an EGS role connection message")
async def test_egsRoleMessage(interaction: discord.Interaction):
    # If you want private responses, set ephemeral to True
    #await interaction.response.send_message(f"{interaction.user.mention} Hello {interaction.user}!", ephemeral=True)

    egsMessageID = await interaction.channel.send("React to this message to apply for special role")
    await egsMessageID.add_reaction("✅")

    # Store this message ID for listener later
    bot.target_message_id = egsMessageID.id
    await interaction.response.send_message("Message sent successfully!", ephemeral= True)


@bot.listen()
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    # Ignore the bots own reaction
    if user.bot:
        return
    
    # Reaction must be from the EGS message
    if reaction.message.id != bot.target_message_id:
        #print("Reaction Ignored")
        return

    print(f"Reaction registered from {user.name} on the target message")


'''
Connection Functions
'''

# Function to print a message to terminal if connected successfully and slash commands are synced
@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user}")

    # Attempt to sync slash commands
    try:
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands.")
    except Exception as e:
        print("Something went wrong while syncing commands: " , e)

#print(os.getcwd())
# Read the token secret from external file, might need to change this directory
with open("token.txt") as f:
    token = f.read()

bot.run(token)