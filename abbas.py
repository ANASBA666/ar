import requests
import asyncio
import discord
from discord.ext import commands
import traceback
import shutil
import os
import sys

# ANSI Colors for clean console output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"

# Static ASCII Art - No animation, just shows up clean
ASCII_ART = f"""
{Colors.RED}
 ░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓███████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
{Colors.RESET}
"""

# Token validation - Quick and dirty
def validate_token(token):
    headers = {"Authorization": token}
    response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
    if response.status_code != 200:
        print(f"{Colors.RED}Invalid token, dipshit.{Colors.RESET}")
        sys.exit()
    user = response.json()
    print(f"{Colors.GREEN}Token good for {user['username']}#{user['discriminator']}{Colors.RESET}")

# FFmpeg check - No fucking around
def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        print(f"{Colors.RED}FFmpeg ain't here, fucker. Get it from [ffmpeg.org](https://ffmpeg.org){Colors.RESET}")
        sys.exit()

# Load the Opus library
def load_opus():
    try:
        if not discord.opus.is_loaded():
            discord.opus.load_opus("/usr/lib64/libopus.so")  # Default path for Amazon Linux
            print(f"{Colors.GREEN}Opus library loaded successfully.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Failed to load Opus library: {str(e)}{Colors.RESET}")
        sys.exit()

# Initialize bot
bot = commands.Bot(command_prefix="!", self_bot=True)

# Global variables to track state
current_vc = None
audio_source = None
FFMPEG_OPTS = {
    'options': '-vn -af "volume=31dB,bass=g=51,highpass=f=100,lowpass=f=8000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09"',
}

# Murder that audio dead
async def murder_audio():
    global current_vc, audio_source
    if current_vc:
        if current_vc.is_playing():
            current_vc.stop()
        await current_vc.disconnect()
        current_vc = None
    audio_source = None

# Change the audio file
async def change_audio(new_file):
    global current_vc, audio_source
    if not os.path.exists(new_file):
        print(f"{Colors.RED}File {new_file} doesn’t exist, you blind fuck.{Colors.RESET}")
        return False

    try:
        new_audio = discord.FFmpegPCMAudio(new_file, **FFMPEG_OPTS)
        if current_vc and current_vc.is_connected():
            if current_vc.is_playing():
                current_vc.stop()
            current_vc.play(new_audio)
            print(f"{Colors.GREEN}Switched to blasting {new_file} in 🔊 {current_vc.channel.name} - LOUD AS FUCK{Colors.RESET}")
            audio_source = new_audio
            return True
        else:
            print(f"{Colors.RED}Bot isn’t in a voice channel, asshole.{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}Failed to change audio to {new_file}: {str(e)}{Colors.RESET}")
        return False

@bot.event
async def on_ready():
    print(ASCII_ART)
    print(f"{Colors.CYAN}Logged in as {bot.user} - Pick server/voice, then use DMs for commands{Colors.RESET}")

    servers = list(bot.guilds)
    if not servers:
        print(f"{Colors.RED}You're not in any servers, dumbass.{Colors.RESET}")
        await bot.close()
        return

    # Display server selection menu
    print(f"\n{Colors.MAGENTA}=== SERVER SELECTION ==={Colors.RESET}")
    print(f"{Colors.YELLOW}Select a server by entering its number:{Colors.RESET}")
    for i, server in enumerate(servers):
        print(f"{Colors.CYAN}{i + 1}. 🏰 {server.name}{Colors.RESET}")
    print(f"{Colors.MAGENTA}========================={Colors.RESET}\n")

    while True:
        try:
            server_choice = int(input(f"{Colors.YELLOW}Enter server number: {Colors.RESET}")) - 1
            if server_choice < 0 or server_choice >= len(servers):
                raise ValueError("Invalid server number, idiot.")
            break
        except ValueError:
            print(f"{Colors.RED}Invalid input. Try again, moron.{Colors.RESET}")

    guild = servers[server_choice]
    print(f"\n{Colors.GREEN}Selected server: 🏰 {guild.name}{Colors.RESET}\n")

    # Get list of voice channels in the selected server
    voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
    if not voice_channels:
        print(f"{Colors.RED}No voice channels found in this server, dumbfuck.{Colors.RESET}")
        await bot.close()
        return

    # Display voice channel selection menu
    print(f"\n{Colors.MAGENTA}=== VOICE CHANNEL SELECTION ==={Colors.RESET}")
    print(f"{Colors.YELLOW}Select a voice channel by entering its number:{Colors.RESET}")
    for i, channel in enumerate(voice_channels):
        user_limit = channel.user_limit if channel.user_limit > 0 else "∞"
        status = f"{Colors.GREEN}✅ OPEN{Colors.RESET}" if len(channel.members) < channel.user_limit else f"{Colors.RED}❌ FULL{Colors.RESET}"
        print(f"{Colors.CYAN}{i + 1}. 🔊 {channel.name} (Users: {len(channel.members)}/{user_limit}, Status: {status}) {Colors.RESET}")
    print(f"{Colors.MAGENTA}==============================={Colors.RESET}\n")

    while True:
        try:
            channel_choice = int(input(f"{Colors.YELLOW}Enter voice channel number: {Colors.RESET}")) - 1
            if channel_choice < 0 or channel_choice >= len(voice_channels):
                raise ValueError("Invalid voice channel number, retard.")
            break
        except ValueError:
            print(f"{Colors.RED}Invalid input. Try again, tool.{Colors.RESET}")

    voice_channel = voice_channels[channel_choice]
    print(f"\n{Colors.GREEN}Joining voice channel: 🔊 {voice_channel.name}{Colors.RESET}\n")

    # Connect to the selected voice channel with retry logic
    retries = 3
    for attempt in range(retries):
        try:
            global current_vc
            current_vc = await voice_channel.connect(reconnect=True, timeout=30)
            print(f"{Colors.GREEN}Successfully connected to 🔊 {voice_channel.name}{Colors.RESET}\n")
            break
        except asyncio.TimeoutError:
            print(f"{Colors.RED}Attempt {attempt + 1}/{retries}: Timeout while connecting to voice channel. Retrying ...{Colors.RESET}")
        except discord.Forbidden:
            print(f"{Colors.RED}ERROR: The bot doesn't have permission to join or speak in this channel.{Colors.RESET}")
            await bot.close()
            return
        except Exception as e:
            print(f"{Colors.RED}CRITICAL FAILURE: Couldn't connect to 🔊 {voice_channel.name}. Error: {str(e)}{Colors.RESET}")
            if attempt == retries - 1:
                await bot.close()
                return
    else:
        print(f"{Colors.RED}Failed to connect to voice channel after {retries} attempts. Exiting...{Colors.RESET}")
        await bot.close()
        return

    # Get the absolute path to the file
    media_url = os.path.abspath("test.mp4")
    print(f"{Colors.YELLOW}Using file: {media_url}{Colors.RESET}")

    # Play the audio in a loop
    try:
        audio_source = discord.FFmpegPCMAudio(media_url, **FFMPEG_OPTS)
        current_vc.play(audio_source)
        print(f"{Colors.GREEN}BLASTING {media_url} IN 🔊 {voice_channel.name} WITH MAX CLARITY AND LOUDNESS - LOOPING FOREVER{Colors.RESET}\n")
        while True:
            await asyncio.sleep(5)  # Reduced from 1 second to lessen spam
            if current_vc.channel != voice_channel:
                print(f"{Colors.YELLOW}Bot moved to a new voice channel: 🔊 {current_vc.channel.name}{Colors.RESET}")
                voice_channel = current_vc.channel
    except discord.ClientException as e:
        print(f"{Colors.RED}FATAL ERROR: Discord client exception: {str(e)}{Colors.RESET}")
        await murder_audio()
    except Exception as e:
        print(f"{Colors.RED}FATAL ERROR: FFmpeg failed to process the file. Error: {str(e)}{Colors.RESET}")
        await murder_audio()
    finally:
        await murder_audio()

@bot.event
async def on_message(message):
    # Only process DMs
    if not isinstance(message.channel, discord.DMChannel):
        return

    # Debug: Minimal print to confirm DM received
    print(f"{Colors.YELLOW}DM from {message.author} (ID: {message.author.id}): {message.content}{Colors.RESET}")

    # Check for !switch command from specific user (replace with your ID if needed)
    if message.content.startswith('!switch') and str(message.author.id) == '1210402608070791230':  # Update this ID if it's not you
        try:
            parts = message.content.split()
            if len(parts) < 2:
                print(f"{Colors.RED}No channel ID provided, dickhead.{Colors.RESET}")
                await message.add_reaction('❌')
                return

            channel_id = int(parts[1])
            print(f"{Colors.YELLOW}Attempting to switch to channel ID: {channel_id}{Colors.RESET}")

            target_channel = bot.get_channel(channel_id)
            if not target_channel:
                print(f"{Colors.RED}Channel {channel_id} doesn’t exist, you blind fuck.{Colors.RESET}")
                await message.add_reaction('❌')
                return

            if not isinstance(target_channel, discord.VoiceChannel):
                print(f"{Colors.RED}Channel {channel_id} isn’t a voice channel, asshole.{Colors.RESET}")
                await message.add_reaction('❌')
                return

            guild = target_channel.guild
            if guild not in bot.guilds:
                print(f"{Colors.RED}Bot isn’t in guild {guild.name}, fucker.{Colors.RESET}")
                await message.add_reaction('❌')
                return

            global current_vc, audio_source
            if current_vc and current_vc.is_playing():
                print(f"{Colors.YELLOW}Saving current audio state.{Colors.RESET}")
                audio_source = discord.FFmpegPCMAudio("test.mp4", **FFMPEG_OPTS)

            await murder_audio()
            print(f"{Colors.YELLOW}Connecting to 🔊 {target_channel.name}{Colors.RESET}")

            retries = 3
            for attempt in range(retries):
                try:
                    current_vc = await target_channel.connect(reconnect=True, timeout=30)
                    print(f"{Colors.GREEN}Switched to 🔊 {target_channel.name} - Audio slamming{Colors.RESET}")
                    current_vc.play(audio_source or discord.FFmpegPCMAudio("test.mp4", **FFMPEG_OPTS))
                    await message.add_reaction('✅')
                    return
                except asyncio.TimeoutError:
                    print(f"{Colors.RED}Attempt {attempt + 1}/{retries}: Timeout switching to {target_channel.name}. Retrying...{Colors.RESET}")
                except discord.Forbidden:
                    print(f"{Colors.RED}No permission to join or speak in {target_channel.name}, motherfucker.{Colors.RESET}")
                    await message.add_reaction('❌')
                    return
                except Exception as e:
                    print(f"{Colors.RED}Switch failed for {target_channel.name}: {str(e)}{Colors.RESET}")
                    if attempt == retries - 1:
                        await message.add_reaction('💥')
                        return

        except ValueError:
            print(f"{Colors.RED}Invalid channel ID format, you dumb prick.{Colors.RESET}")
            await message.add_reaction('❌')
        except Exception as e:
            print(f"{Colors.RED}Switch command fucked up: {str(e)}{Colors.RESET}")
            await message.add_reaction('💥')

    # Check for !change command to switch audio file from specific user (replace with your ID if needed)
    if message.content.startswith('!change') and str(message.author.id) == '1210402608070791230':  # Update this ID if it's not you
        try:
            parts = message.content.split()
            if len(parts) < 2:
                print(f"{Colors.RED}No audio file provided, dickhead.{Colors.RESET}")
                await message.add_reaction('❌')
                return

            new_file = parts[1]
            print(f"{Colors.YELLOW}Attempting to change audio to: {new_file}{Colors.RESET}")

            if await change_audio(new_file):
                await message.add_reaction('✅')
            else:
                await message.add_reaction('❌')

        except Exception as e:
            print(f"{Colors.RED}Change command fucked up: {str(e)}{Colors.RESET}")
            await message.add_reaction('💥')

token = "MTIwMTkwNDY4NjE0ODM2MjM3MQ.GLEv8E.QE5mBGrh9X8L91vJLdwWu2YRP-IkJlFg3Z9ptE"

if __name__ == "__main__":
    print(ASCII_ART)
    check_ffmpeg()
    load_opus()
    validate_token(token)
    bot.run(token)
