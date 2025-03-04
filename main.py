import discord
from discord.ext import commands
from discord import app_commands
import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use the secret environment variables for the token and database connection
TOKEN = os.getenv("TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Setup intents and bot
intents = discord.Intents.default()
intents.members = True  # Enable the members intent to listen to member updates

bot = commands.Bot(command_prefix='!', intents=intents)

# Store previous names in a dictionary
previous_names = {}

# MySQL database connection function
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# On bot startup
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
        for command in synced_commands:
            print(f'Synced command: {command.name}')
    except Exception as e:
        print(f'Error syncing commands: {e}')

# On member update (detects nickname change)
@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        channel = discord.utils.get(after.guild.text_channels, name='invfed-bot-testing')
        if channel is None:
            print("Channel 'invfed-bot-testing' not found.")
            return

        embed = discord.Embed(title="Name Change Notification", color=discord.Color.blue())
        embed.add_field(name="Discord ID", value=f"<@{after.id}>", inline=False)
        embed.add_field(name="Current Username", value=after.name, inline=False)

        # Update previous names in dictionary
        if after.id in previous_names:
            previous_names[after.id].append(before.nick)
        else:
            previous_names[after.id] = [before.nick] if before.nick else []

        embed.add_field(name="Previous Names", value="\n".join(previous_names[after.id]), inline=False)
        embed.set_thumbnail(url=after.avatar.url if after.avatar else None)

        # Log the name change to the database
        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                query = "SELECT COUNT(*) FROM name_changes WHERE user_id = %s AND previous_name = %s"
                cursor.execute(query, (after.id, before.nick))
                result = cursor.fetchone()

                if result[0] == 0:  # Avoid inserting duplicates
                    insert_query = "INSERT INTO name_changes (user_id, previous_name, current_name) VALUES (%s, %s, %s)"
                    cursor.execute(insert_query, (after.id, before.nick, after.nick))
                    connection.commit()
                    print(f"Inserted name change for {after.id}")
                else:
                    print(f"Duplicate name change detected for {after.id}")
                
                cursor.close()
                connection.close()
        except mysql.connector.Error as e:
            print(f"Error while inserting data into the database: {e}")

        # Delete the old message if it exists
        async for message in channel.history(limit=100):
            if message.embeds and message.embeds[0].title == "Name Change Notification" and message.embeds[0].fields[0].value == f"<@{after.id}>":
                await message.delete()
                break

        await channel.send(embed=embed)

# Slash command to set the notification channel
@bot.tree.command(name="setnamechange", description="Set the channel for name change notifications.")
@app_commands.describe(channel="The channel for notifications")
async def set_name_change(interaction: discord.Interaction, channel: discord.TextChannel):
    global notification_channel
    notification_channel = channel
    await interaction.response.send_message(f"Name change notifications will be sent to {channel.mention}.", ephemeral=True)

# Slash command to check name changes for a user
@bot.tree.command(name="checknamechanges", description="Check all name changes for a user.")
@app_commands.describe(member="The member to check")
async def check_name_changes(interaction: discord.Interaction, member: discord.Member):
    if member.id in previous_names:
        name_changes = "\n".join(previous_names[member.id])
        await interaction.response.send_message(f"Previous names for {member.mention}:\n{name_changes}", ephemeral=True)
    else:
        await interaction.response.send_message(f"No previous names found for {member.mention}.", ephemeral=True)

# Start the bot
bot.run(TOKEN)
