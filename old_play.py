@client.command(pass_context=True,brief="Playing/adding to the queue music/video (from youtube).")
async def play(ctx, *, search_term: str):
  if not ctx.author.voice:
    await ctx.send("You are not in a voice channel...")
  elif not ctx.voice_client:
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.guild.change_voice_state(channel=channel,self_mute=False,self_deaf=True)
  try:
    search_term = search_term[:43]
    with ytdl as ydl:
      search_url = f"ytsearch:{search_term}"
      info = ydl.extract_info(search_url, download=False)
      if 'entries' in info:
        video_url = info['entries'][0]['url']
        video_title = info['entries'][0]['title']

        song = Song(video_title, video_url)
        song_queue.append(song)

        if not ctx.voice_client.is_playing(
        ) and not ctx.voice_client.is_paused():
          await play_song(ctx)
        else:
          await ctx.send(f"Added '{song.title}' to the queue.")
      else:
        await ctx.send("No results found.")
  except Exception as e:
    await ctx.send(f"An error occurred: {str(e)}")