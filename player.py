import vlc
def play(path):

    instance = vlc.Instance()

    # Create a MediaPlayer with the default instance
    player = instance.media_player_new()

    # Load the media file
    media = instance.media_new(path)

    # Add the media to the player
    player.set_media(media)
    player.set_position(60)
    player.audio_set_volume(65)

    # Play for 10 seconds then exit
    player.play()

