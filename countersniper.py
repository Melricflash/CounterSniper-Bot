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

'''
Classes
'''
class EGSModal(discord.ui.Modal, title="FN Customs Application"):
    egsForm = discord.ui.TextInput(
        label='EGS Username',
        placeholder='Enter your EGS Username exactly as its spelt, you cannot do this later'
    )

    # To retrieve the information from the form, we handle it in this function
    async def on_submit(self, interaction: discord.Interaction):

        # Retrieve submitted EGS username and Discord Username
        egsUsername = self.egsForm.value
        discordUsername = interaction.user.name

        print(f"Data received from {discordUsername}: {egsUsername}")

        # Next we want to pass to a function that will store this in a database if name doesnt exist
        DBstatus = saveToDB(discordUsername, egsUsername, 'discordEgs.csv')

        if DBstatus == 1:
            await interaction.response.send_message(f'An application was already submitted for either Discord: {discordUsername} or EGS: {egsUsername}', ephemeral=True)
            return
        
        await interaction.response.send_message(f'Your application was submitted!', ephemeral=True)

        # TODO: Handle adding user to role


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
def saveToDB(discName, EGSName, fileName):

    filename = fileName
    data = {'DiscordUsername': [discName], 'EGSUsername': [EGSName]}

    # Create a new file if it doesnt exist
    if not os.path.exists(filename):
        df = pd.DataFrame(data)
        df.to_csv(filename, index = False)

    else:
        df = pd.read_csv(filename)
        
        # Check if an entry exists
        if df['DiscordUsername'].isin([discName]).any() or df['EGSUsername'].isin([EGSName]).any():
            print(f"An application was already submitted for either Discord: {discName} or EGS: {EGSName}")
            return 1

        # Update the database
        else:
            tempFrame = pd.DataFrame(data)
            df = pd.concat([df, tempFrame], ignore_index=True)

            df.to_csv(filename, index=False)


        
'''
Async Functions
'''


@bot.tree.command(name = "test_egs_modal", description="Requests EGS Form")
async def create_EGS_Message(interaction: discord.Interaction):
    view = EGSView()
    await interaction.response.send_message("To Join Fortnite Custom Games, you must provide your Epic Games Account Username, press the button below to do this:\n", view=view)


# Function to create a message when reacted to will open a form to fill in EGS account info
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