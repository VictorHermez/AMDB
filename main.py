import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from dotenv import load_dotenv  # ✅ Added to load .env variables

load_dotenv()  # ✅ Initialize dotenv to load the .env file

TOKEN = os.getenv("TOKEN")  # ✅ Load the TOKEN from the .env file

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
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready.")

# (Continue the rest of your code here...)

# ✅ Run the bot with the loaded token
bot.run(TOKEN)
