import music_tag
class ID3Editor():

    def after(value, a):
        # Find and validate first part.
        pos_a = value.rfind(a)
        if pos_a == -1: return ""
        # Returns chars after the found string.
        adjusted_pos_a = pos_a + len(a)
        if adjusted_pos_a >= len(value): return ""
        return value[adjusted_pos_a:]

    def before(value, a):

        # Find first part and return slice before it.
        pos_a = value.find(a)
        if pos_a == -1: return ""
        return value[0:pos_a]

    def main_id3(path):
        audiofile = music_tag.load_file(path)
        comment = audiofile['comment']
        com = str(comment)
        genres = ID3Editor.after(com, "- ")
        comment_split_by_space = com.split(" ")
        key = comment_split_by_space[0]
        energy = comment_split_by_space[2]

        """THIS MAY BE CAUSING PROBLEMS WORK ON IN FUTURE"""
        comment_split_by_comma = genres.split(", ")

        categories = []
        for item in comment_split_by_comma:
            categories.append(item)

        return categories, key, energy

    def id3_write(path, string):
        audiofile = music_tag.load_file(path)
        audiofile['comment'] = string
        audiofile.save()

    def get_details(path):
        audiofile = music_tag.load_file(path)
        title = audiofile['title']
        artist = audiofile['artist']
        if str(artist) == "":
            artist = str(audiofile['albumartist']) + " [Album Artist]"
        return title, artist