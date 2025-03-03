import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

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

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready.")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="setnamechange", description="Set the channel for name change updates.")
@app_commands.checks.has_permissions(administrator=True)
async def setnamechange(interaction: discord.Interaction, channel: discord.TextChannel):
    data = load_data()
    data["channel_id"] = channel.id
    save_data(data)
    await interaction.response.send_message(f"Name change updates will be sent in {channel.mention}.", ephemeral=True)

# ✅ Run the bot with the loaded token
bot.run(TOKEN)
