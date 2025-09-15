import discord
from discord.ext import commands
import os
import sys
import json

# Replace with your Discord user ID
BOT_OWNER_ID = 123456789012345678  

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Remove the default help command so we can make our own
bot.remove_command("help")

# ========== FILE STORAGE ==========
WHITELIST_FILE = "whitelist.json"
STATUS_FILE = "status.json"

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r") as f:
            return json.load(f)
    return []

def save_whitelist(whitelist):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(whitelist, f)

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"type": "playing", "text": "Hello! I'm online."}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    status = load_status()
    activity_type = getattr(discord.ActivityType, status["type"], discord.ActivityType.playing)
    await bot.change_presence(activity=discord.Activity(type=activity_type, name=status["text"]))

# ========== PERMISSION CHECK ==========
def is_owner_or_admin():
    async def predicate(ctx):
        whitelist = load_whitelist()
        if ctx.author.id == BOT_OWNER_ID:
            return True
        if ctx.author.guild_permissions.administrator:
            return True
        if ctx.author.id in whitelist:
            return True
        return False
    return commands.check(predicate)

# ========== MODERATION COMMANDS ==========
@bot.command()
@is_owner_or_admin()
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick a member."""
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked.")

@bot.command()
@is_owner_or_admin()
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban a member."""
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned.")

@bot.command()
@is_owner_or_admin()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    """Give a role to a member."""
    await member.add_roles(role)
    await ctx.send(f"✅ {role.name} role added to {member.mention}")

@bot.command()
@is_owner_or_admin()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    """Remove a role from a member."""
    await member.remove_roles(role)
    await ctx.send(f"❌ {role.name} role removed from {member.mention}")

# ========== OWNER ONLY COMMANDS ==========
@bot.command()
async def shutdown(ctx):
    """Shut down the bot (Owner only)."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can shut me down.")
        return
    await ctx.send("👋 Shutting down...")
    await bot.close()

@bot.command()
async def restart(ctx):
    """Restart the bot (Owner only)."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can restart me.")
        return
    await ctx.send("🔄 Restarting bot...")
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)  # Re-run the bot script

# ========== INFO COMMANDS ==========
@bot.command()
@is_owner_or_admin()
async def status(ctx):
    """Check if the bot is online (Owner/Admin/Whitelist only)."""
    await ctx.send("✅ I'm online and ready!")

@bot.command()
@is_owner_or_admin()
async def serverinfo(ctx):
    """Show server information."""
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 Server Info: {guild.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="🆔 Server ID", value=guild.id, inline=False)
    embed.add_field(name="👑 Owner", value=guild.owner, inline=False)
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="📂 Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="📅 Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await ctx.send(embed=embed)

@bot.command()
@is_owner_or_admin()
async def userinfo(ctx, member: discord.Member = None):
    """Show user information."""
    member = member or ctx.author
    roles = [role.mention for role in member.roles if role.name != "@everyone"]

    embed = discord.Embed(
        title=f"👤 User Info: {member}",
        color=discord.Color.green()
    )
    embed.add_field(name="🆔 User ID", value=member.id, inline=False)
    embed.add_field(name="📛 Nickname", value=member.display_name, inline=True)
    embed.add_field(name="📅 Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="📅 Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="📂 Roles", value=", ".join(roles) if roles else "No roles", inline=False)
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)

    await ctx.send(embed=embed)

@bot.command()
@is_owner_or_admin()
async def ping(ctx):
    """Check bot latency."""
    latency = round(bot.latency * 1000)  # convert to ms
    await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

# ========== STATUS MANAGEMENT ==========
@bot.command()
async def setstatus(ctx, stype: str, *, text: str):
    """Set the bot's status (Owner only). Types: playing, listening, watching, competing"""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can change my status.")
        return

    stype = stype.lower()
    if stype not in ["playing", "listening", "watching", "competing"]:
        await ctx.send("⚠️ Invalid status type. Use: playing, listening, watching, competing")
        return

    activity_type = getattr(discord.ActivityType, stype, discord.ActivityType.playing)
    await bot.change_presence(activity=discord.Activity(type=activity_type, name=text))

    save_status({"type": stype, "text": text})
    await ctx.send(f"✅ Status updated to **{stype} {text}**")

# ========== WHITELIST MANAGEMENT ==========
@bot.command()
async def addwhitelist(ctx, member: discord.Member):
    """Owner only: Add a user to the whitelist."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can manage the whitelist.")
        return

    whitelist = load_whitelist()
    if member.id in whitelist:
        await ctx.send(f"⚠️ {member.mention} is already whitelisted.")
    else:
        whitelist.append(member.id)
        save_whitelist(whitelist)
        await ctx.send(f"✅ {member.mention} has been added to the whitelist.")

@bot.command()
async def removewhitelist(ctx, member: discord.Member):
    """Owner only: Remove a user from the whitelist."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can manage the whitelist.")
        return

    whitelist = load_whitelist()
    if member.id not in whitelist:
        await ctx.send(f"⚠️ {member.mention} is not whitelisted.")
    else:
        whitelist.remove(member.id)
        save_whitelist(whitelist)
        await ctx.send(f"❌ {member.mention} has been removed from the whitelist.")

@bot.command()
async def showwhitelist(ctx):
    """Owner only: Show all whitelisted users."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can view the whitelist.")
        return

    whitelist = load_whitelist()
    if not whitelist:
        await ctx.send("📭 Whitelist is empty.")
    else:
        mentions = [f"<@{uid}>" for uid in whitelist]
        await ctx.send("✅ Whitelisted users:\n" + "\n".join(mentions))

# ========== HELP COMMAND ==========
@bot.command()
async def help(ctx):
    """Show custom help message."""
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="🔨 Moderation",
        value="`!kick @user [reason]`\n`!ban @user [reason]`\n`!addrole @user @role`\n`!removerole @user @role`",
        inline=False
    )
    embed.add_field(
        name="⚙️ Owner Only",
        value="`!shutdown`\n`!restart`\n`!setstatus <type> <text>`\n`!addwhitelist @user`\n`!removewhitelist @user`\n`!showwhitelist`",
        inline=False
    )
    embed.add_field(
        name="📊 Info",
        value="`!status`\n`!serverinfo`\n`!userinfo [@user]`\n`!ping`",
        inline=False
    )
    embed.set_footer(text="✅ Only Owner/Admin/Whitelisted users can use most commands.")

    await ctx.send(embed=embed)

# ========== RUN BOT ==========
bot.run("YOUR_BOT_TOKEN")
