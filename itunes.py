from libpytunes import Library


def playlist_list(playlist_name, itunes_xml):
    lib = Library(itunes_xml)
    playlist = lib.getPlaylist(playlist_name)
    track_locations = []
    for song in playlist.tracks:
        # print("{a} - {n} - {p}".format(a=song.artist, n=song.name, p=song.location))
        track_locations.append(song.location)
    return track_locations


if __name__ == '__main__':
    playlist_name = "Sort"
    itunes_xml = "/Users/dan/Music/Music/Library.xml"
    playlist_list(playlist_name, itunes_xml)
