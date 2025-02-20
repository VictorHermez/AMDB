import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# Bot setup with intents
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# File to store user data and channel info
DATA_FILE = "bot_data.json"
CHANNEL_ID = None

# Load or initialize data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "channel_id": None}

# Save data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Create or update an embed for a user
async def update_user_embed(channel, user_id, current_name, past_names, message_id=None):
    embed = discord.Embed(title=f"Name History for {current_name}", color=discord.Color.blue())
    embed.add_field(name="User ID", value=user_id, inline=False)
    embed.add_field(name="Current Name", value=current_name, inline=False)
    embed.add_field(name="Past Names", value=", ".join(past_names) if past_names else "None", inline=False)
    
    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)
            return message_id
        except discord.NotFound:
            pass
    
    msg = await channel.send(embed=embed)
    return msg.id

# On bot startup
@bot.event
async def on_ready():
    global CHANNEL_ID
    print(f"Logged in as {bot.user}")
    data = load_data()
    CHANNEL_ID = data["channel_id"]

    if CHANNEL_ID:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("Stored channel not found!")
            return

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Track name changes
@bot.event
async def on_member_update(before, after):
    if before.nick == after.nick and before.name == after.name:
        return

    if not CHANNEL_ID:
        return

    data = load_data()
    user_data = data["users"]
    user_id = str(before.id)

    if user_id not in user_data:
        user_data[user_id] = {"current_name": before.name, "past_names": [], "message_id": None}
    
    old_name = before.name
    new_name = after.name
    if old_name != new_name:
        if "past_names" not in user_data[user_id]:
            user_data[user_id]["past_names"] = []
        if old_name not in user_data[user_id]["past_names"]:
            user_data[user_id]["past_names"].append(old_name)
        user_data[user_id]["current_name"] = new_name

        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            message_id = user_data[user_id]["message_id"]
            new_message_id = await update_user_embed(
                channel,
                user_id,
                new_name,
                user_data[user_id]["past_names"],
                message_id
            )
            user_data[user_id]["message_id"] = new_message_id

    data["users"] = user_data
    save_data(data)

# Slash command to set the channel
@app_commands.command(name="setchannel", description="Set the channel for name history embeds")
@app_commands.checks.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global CHANNEL_ID
    data = load_data()
    
    CHANNEL_ID = channel.id
    data["channel_id"] = CHANNEL_ID
    
    user_data = data["users"]
    for user_id, info in user_data.items():
        message_id = await update_user_embed(
            channel,
            user_id,
            info["current_name"],
            info["past_names"],
            None
        )
        user_data[user_id]["message_id"] = message_id
    
    data["users"] = user_data
    save_data(data)
    await interaction.response.send_message(f"Name history embeds will now appear in {channel.mention}", ephemeral=True)

@set_channel.error
async def set_channel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You need administrator permissions to use this command!", ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred. Please try again.", ephemeral=True)

# Run the bot with token from environment variable
bot.run(os.getenv("TOKEN"))
