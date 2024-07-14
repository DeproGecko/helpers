import discord
from discord.ext import commands, tasks
import itertools
import json
import asyncio
import os

# Load configuration from file
with open('config.json') as config_file:
    config = json.load(config_file)

# Get your bot's token from environment variables
TOKEN = os.getenv("DISCORD_TOKEN")

# Status messages
status_messages = config["status_rotation"]["status_messages"]

# Create an instance of Intents
intents = discord.Intents.default()
intents.presences = True
intents.guilds = True
intents.messages = True  # Enable message intents

# Initialize the Bot with intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Function to rotate through status messages
@tasks.loop(seconds=10)
async def rotate_status():
    print("rotate_status loop started")  # Debugging output
    for status in itertools.cycle(status_messages):
        print(f"Changing status to: {status}")  # Debugging output
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status))
        await asyncio.sleep(10)  # Use asyncio.sleep instead of discord.utils.sleep_until

# Function to maintain sticky message
@tasks.loop(seconds=10)
async def maintain_sticky_message():
    channel_id = int(config["sticky_message"]["channel_id"])
    sticky_msg = config["sticky_message"]["sticky_message"]

    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found.")
        return

    async for message in channel.history(limit=10):
        if message.author == bot.user and message.content == sticky_msg:
            # If the sticky message is already at the bottom, do nothing
            if message == await channel.fetch_message(channel.last_message_id):
                return
            else:
                await message.delete()

    # Send the sticky message
    await channel.send(sticky_msg)

# Event to run when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    # Start rotating status
    rotate_status.start()

    # Start maintaining sticky message
    maintain_sticky_message.start()

    print("Bot is ready.")

# Nuke command to recreate the current channel
@bot.command(name="nuke", description="Nuke the current channel and recreate it.")
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    channel = ctx.channel

    allowed_category_id = int(config["nuke_command"]["allowed_category_id"])

    if channel.category and channel.category.id == allowed_category_id:
        position = channel.position
        new_channel = await channel.clone()
        await new_channel.edit(position=position)
        await channel.delete()

        user_id = int(config["nuke_command"]["user_id"])
        emoji = config["nuke_command"]["emoji"]
        await new_channel.send(f'Chat nuked by <@{user_id}> {emoji}')
        await ctx.send(f'Channel nuked and recreated: {new_channel.mention}')
    else:
        await ctx.send('This command can only be used in the specified category.')

# Run the bot
bot.run(TOKEN)
