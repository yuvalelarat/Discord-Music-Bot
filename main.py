import discord
import yt_dlp as youtube_dl
import os
from discord.ext import commands
#from webserver import keep_alive
from dotenv import load_dotenv


def configure():
    load_dotenv()

configure()

class Song:
    def __init__(self, title, url):
        self.title = title
        self.url = url
 
        
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

voice_clients = {}

song_queue = []

yt_dl_opts = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'options:' '-vn'}

is_playing = False

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown command. Type `!help` to see the list of available commands.\nsNol might add more in the future you can send him suggestions.")
    
@client.command(brief="Say to the bot hi.")
async def hi(ctx):
    if ctx.author != client.user:
        await ctx.send(f"Hi, {ctx.author.display_name}")
        
@client.command(brief="Say hi to the bot in hebrew.")
async def shalom(ctx):
    if ctx.author != client.user:
        await ctx.send(f"Shalom, {ctx.author.display_name}")
        
@client.command(pass_context=True, brief="Joins channel.")
async def join(ctx):
  if (ctx.author.voice):
    channel = ctx.message.author.voice.channel
    await channel.connect()
    await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)
  else:
    await ctx.send("You are not in a voice channel dumbass...")

@client.command(pass_context = True, brief="leaves channel.")
async def leave(ctx):
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        await ctx.send('Ah ok bye') 
    else:
        await ctx.send("WTF i'm not in a voice channel idiot...")

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>MUSIC COMMANDS<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@client.command(pass_context=True, brief="Playing/adding to the queue music/video (from youtube or playlist).")
async def play(ctx, *, search_term: str):
    if not ctx.author.voice:
        await ctx.send("You are not in a voice channel...")
    elif not ctx.voice_client:
        channel = ctx.author.voice.channel
        await channel.connect()

    try:
        with ytdl as ydl:
            if "list" in search_term:
                await ctx.send("You sent me a playlist, please hold on a few min so i can add all the songs from the playlist to the queue")
                info = ydl.extract_info(search_term, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        video_url = entry['url']
                        video_title = entry['title']
                        song = Song(video_title, video_url)
                        song_queue.append(song)
                    
                    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                        await play_song(ctx)
                    else:
                        await ctx.send(f"Added {len(info['entries'])} videos from the playlist to the queue.")
                else:
                    await ctx.send("No videos found in the playlist.")
            else:
                search_term = search_term[:43]
                search_url = f"ytsearch:{search_term}"
                info = ydl.extract_info(search_url, download=False)
                if 'entries' in info:
                    video_url = info['entries'][0]['url']
                    video_title = info['entries'][0]['title']

                    song = Song(video_title, video_url)
                    song_queue.append(song)

                    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                        await play_song(ctx)
                    else:
                        await ctx.send(f"Added '{song.title}' to the queue.")
                else:
                    await ctx.send("No results found.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

async def play_song(ctx):
    global is_playing
    
    # Only proceed if play_song is not already running
    if not is_playing:
        is_playing = True

        if song_queue:
            song = song_queue.pop(0)
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
            }

            def after_playing(error):
                global is_playing  # Mark play_song as finished
                if error:
                    print(f"An error occurred while playing: {error}")
                ctx.voice_client.stop()  
                is_playing = False  # Reset the flag
                client.loop.create_task(play_song(ctx))  # Play next song if available

            ctx.voice_client.play(discord.FFmpegPCMAudio(song.url, **FFMPEG_OPTIONS), after=after_playing)
            await ctx.send(f"Now playing: {song.title}")
        else:
            await ctx.send("Queue is empty.")
            is_playing = False  # Reset the flag


@client.command(pass_context=True, brief="Pausing the sound/music.")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Playback paused.")
    else:
        await ctx.send("No audio is currently playing or the bot is not in a voice channel, are you really that stupid?")

@client.command(pass_context=True, brief="Resuming the sound/music.")
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Playback resumed.")
    else:
        await ctx.send("No audio is paused or the bot is not in a voice channel, do you even got a brain?")

@client.command(pass_context=True, brief="Skipping to the next track/video.")
async def skip(ctx):
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop()
        await ctx.send("Skipped the current song.")
        await play_song(ctx)
    else:
        await ctx.send("No song is currently playing or paused.")

        
@client.command(pass_context=True, brief="Stoping the track/video.")
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        song_queue.clear() 
        await ctx.send("Playback stopped and queue cleared.")
    else:
        await ctx.send("No audio is playing or the bot is not in a voice channel.")

@client.command(brief="Display the queue of videos/tracks.")
async def queue(ctx):
    if not song_queue:
        await ctx.send("The queue is empty.")
    else:
        queue_message = "Queue:\n"
        for index, song in enumerate(song_queue, start=1):
            queue_message += f"{index}. {song.title}\n"
        await ctx.send(queue_message)


client.run(os.getenv('token'))