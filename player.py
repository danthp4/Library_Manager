import vlc


def play(path):
    instance = vlc.Instance()

    # Create a MediaPlayer with the default instance
    play.player = instance.media_player_new()

    # Load the media file
    media = instance.media_new(path)

    # Add the media to the player
    play.player.set_media(media)
    play.player.audio_set_volume(65)

    # Play for 10 seconds then exit
    play.player.play()
    play.player.set_position(0.35)


def stop(path):
    play.player.stop()
