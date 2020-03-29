import eyed3


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

    def main():

        audiofile = eyed3.load("song_directory/07 Melting Point.mp3")
        print(f"# comments: {len(audiofile.tag.comments)}")
        for comment in audiofile.tag.comments:
            # Show comment
            print(comment.description)
            print(comment.text)
            com = comment.text
            genres = ID3Editor.after(com, "- ")
            comment_split_by_space = com.split(" ")
            key = comment_split_by_space[0]
            energy = comment_split_by_space[2]
            comment_split_by_comma = genres.split(", ")
            for item in comment_split_by_comma:
                print(item)
        print(key, '-', energy, '-', ', '.join(map(str, comment_split_by_comma)))

        audiofile.tag.comments.set("Techno, House, Funk, Soul")
        print(f"# comments (after remove): {len(audiofile.tag.comments)}")
        for comment in audiofile.tag.comments:
            # Show comment
            print(comment.description)
            print(comment.text)


if __name__ == "__main__":
    ID3Editor.main()
