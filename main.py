import discord
from discord.ext import commands
from discord import app_commands
import os
import json

TOKEN = os.getenv("TOKEN")  # Use the secret environment variable for the token

intents = discord.Intents.default()
intents.members = True  # Enable the members intent to listen to member updates

bot = commands.Bot(command_prefix='!', intents=intents)

# Store previous names in a dictionary
previous_names = {}

# File to store user data for previous names
DATA_FILE = "previous_names.json"

# Load or initialize previous names data
def load_previous_names():
    global previous_names
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            previous_names = json.load(f)
    else:
        previous_names = {}

# Save previous names data
def save_previous_names():
    with open(DATA_FILE, 'w') as f:
        json.dump(previous_names, f, indent=4)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.invisible)  # Set bot as offline
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'Bot is in guilds: {[guild.name for guild in bot.guilds]}')

    # Sync commands globally
    try:
        await bot.tree.sync()
        synced_commands = bot.tree.get_commands()
        print(f'Synced {len(synced_commands)} command(s) globally.')

        # Log the names of synced commands
        for command in synced_commands:
            print(f'Synced command: {command.name}')
    except Exception as e:
        print(f'Error syncing commands: {e}')


@bot.event
async def on_member_update(before, after):
    # Check if the nickname has changed
    if before.nick != after.nick:
        # Set the notification channel
        channel = discord.utils.get(after.guild.text_channels, name='invfed-bot-testing')
        if channel is None:
            print("Channel 'invfed-bot-testing' not found.")
            return

        # Prepare the embed message
        embed = discord.Embed(title="Name Change Notification", color=discord.Color.blue())
        embed.add_field(name="Discord ID", value=f"<@{after.id}>", inline=False)
        embed.add_field(name="Current Username", value=after.name, inline=False)

        # Update previous names
        if after.id in previous_names:
            previous_names[after.id].append(before.nick)
        else:
            previous_names[after.id] = [before.nick] if before.nick else []

        embed.add_field(name="Previous Names", value="\n".join(previous_names[after.id]), inline=False)
        embed.set_thumbnail(url=after.avatar.url if after.avatar else None)

        # Delete the old message if it exists and has similar content
        async for message in channel.history(limit=100):
            if message.embeds and message.embeds[0].title == "Name Change Notification" and message.embeds[0].fields[0].value == f"<@{after.id}>":
                await message.delete()
                break

        # Send the updated name change embed
        await channel.send(embed=embed)
        save_previous_names()  # Save the updated names to file


@bot.tree.command(name="setnamechange", description="Set the channel for name change notifications.")
@app_commands.describe(channel="The channel for notifications")
async def set_name_change(interaction: discord.Interaction, channel: discord.TextChannel):
    # Check for permissions (only admins can use this)
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    global notification_channel
    notification_channel = channel
    await interaction.response.send_message(
        f"Name change notifications will be sent to {channel.mention}.", ephemeral=True)


@bot.tree.command(name="checknamechanges", description="Check all name changes for a user.")
@app_commands.describe(member="The member to check")
async def check_name_changes(interaction: discord.Interaction, member: discord.Member):
    if member.id in previous_names:
        name_changes = "\n".join(previous_names[member.id])
        await interaction.response.send_message(
            f"Previous names for {member.mention}:\n{name_changes}",
            ephemeral=True)
    else:
        await interaction.response.send_message(
            f"No previous names found for {member.mention}.", ephemeral=True)


# Start the bot and load previous names data
load_previous_names()
bot.run(TOKEN)
 