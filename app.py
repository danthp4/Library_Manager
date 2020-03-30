import copy
from tkinter import *
import eyed3, app
from excel_import import ExcelImport
from itunes import playlist_list
from player import play, stop


class Checkbar(Frame):
    def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
        Frame.__init__(self, parent)
        self.vars = []
        var = IntVar()
        # check picks to see if category is used, if not put in ""additional" column
        for pick in picks:
            for value in main.cat:
                if value == pick:
                    var = IntVar(value=1)
                    chk = Checkbutton(self, text=pick, variable=var)
                    chk.select()
                    chk.pack(side=side, anchor=anchor, expand=YES)
                    self.vars.append(var)
            if pick not in main.cat:
                var = IntVar()
                chk = Checkbutton(self, text=pick, variable=var)
                chk.pack(side=side, anchor=anchor, expand=YES)
                self.vars.append(var)

    def state(self):
        return map((lambda var: var.get()), self.vars)


def allstates():
    # To get state output as list un-comment below
    """for i in range(len(main.input_ncd)):
        x = main.dict.get(main.input_ncd[i])
        print(str(main.input_ncd[i]), list(x.state()))"""
    # check string output of checkbox changes
    main.checked_cat = []
    for i in range(len(main.input_ncd)):
        state_list = main.dict.get(main.input_ncd[i]).state()
        j = 0
        for value in state_list:
            if value == 1:
                main.checked_cat.append(main.input_array[i][j])
            j += 1
    final_output = str(main.key + ' - ' + main.energy + ' - ' + ', '.join(map(str, main.checked_cat)))
    print('Check: ' + final_output)
    main.update.set(final_output)
    return final_output


def write():
    # write checkbox changes to file and print
    main.checked_cat = []
    for i in range(len(main.input_ncd)):
        state_list = main.dict.get(main.input_ncd[i]).state()
        j = 0
        for value in state_list:
            if value == 1:
                main.checked_cat.append(main.input_array[i][j])
            j += 1
    final_output = str(main.key + ' - ' + main.energy + ' - ' + ', '.join(map(str, main.checked_cat)))
    print('Wrote: ' + final_output)
    ID3Editor.id3_write(main.audio_path, final_output)


def close_inst(audio_path):
    # stop audio and write to file on close
    stop(audio_path)
    additional_collector()
    write()
    main.root.destroy()


def disable_event():
    # for stopping accidental close via window x
    pass


def main(excel_file, audio_path):
    # initialise variables
    main.audio_path = audio_path
    input_file = excel_file
    data = ExcelImport(input_file)
    main.input_array = data.array()
    data.ncd.append('Additional')
    main.input_ncd = data.ncd
    main.dict = {}

    # tkinkter window options
    main.root = Tk()
    main.root.protocol("WM_DELETE_WINDOW", disable_event)
    main.root.title("DJ library editor")

    # get details from eyed3 for audio file
    id3_output = ID3Editor.main_id3(audio_path)
    main.cat = id3_output[0]
    main.key = id3_output[1]
    main.energy = id3_output[2]
    details = ID3Editor.get_details(audio_path)
    song_title = details[0]
    artist = details[1]

    # start playback of file on open
    play(audio_path)

    # copy category list so program can later deterimin leftover categories
    main.leftover_cat = copy.copy(main.cat)

    # initalise string update in window
    main.update = StringVar()

    # draw labels
    fm = Frame(main.root)
    for item in main.input_ncd:
        Label(fm, text=item, relief=GROOVE, bd=5).pack(side=TOP, anchor=W, fill=X)
    fm.pack(side=LEFT, padx=10)

    # check categories for leftovers and remove used categories from leftover_cat
    for list in main.input_array:
        for item in list:
            for value in main.cat:
                if value == item:
                    main.leftover_cat.remove(value)
    main.input_array.append(main.leftover_cat)

    print(main.leftover_cat)

    # draw checkboxes
    fm2 = Frame(main.root)
    i = 0
    for item in main.input_array:
        main.dict[main.input_ncd[i]] = Checkbar(fm2, item)
        main.dict[main.input_ncd[i]].pack(side=TOP, anchor=W, fill=X)
        main.dict[main.input_ncd[i]].config(relief=GROOVE, bd=1)
        i += 1
    fm2.pack(side=LEFT, padx=10)

    # draw user buttons
    fm3 = Frame(main.root)
    Button(fm3, text='Next', command=lambda: close_inst(audio_path)).pack(side=RIGHT)
    Button(fm3, text='Check states', command=allstates).pack(side=RIGHT)
    Button(fm3, text='Write', command=lambda: write()).pack(side=RIGHT)
    Button(fm3, text="Play", command=lambda: play(audio_path)).pack(side=RIGHT)
    Button(fm3, text="Stop", command=lambda: stop(audio_path)).pack(side=RIGHT)
    fm3.pack(side=RIGHT, padx=10)

    # draw eyed3 info labels
    fm4 = Frame(main.root)
    Label(fm4, text=audio_path, relief=GROOVE, bd=2).pack(side=BOTTOM, anchor=W, fill=X)
    Label(fm4, text=artist, relief=GROOVE, bd=2).pack(side=BOTTOM, anchor=W, fill=X)
    Label(fm4, text=song_title, relief=GROOVE, bd=2).pack(side=BOTTOM, anchor=W, fill=X)
    Label(fm4, textvariable=main.update, relief=SOLID, bd=2).pack(side=BOTTOM, anchor=W, fill=X)
    fm4.pack(side=LEFT, padx=10)
    # update string representation
    allstates()

    # draw tkinter
    main.root.mainloop()


def additional_collector():
    additional_collector.add_list = []
    f = open("add.txt", "a+")
    for item in main.leftover_cat:
        f.write("\n" + item)
        additional_collector.add_list.append(item)


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
        audiofile = eyed3.load(path)
        for comment in audiofile.tag.comments:
            com = comment.text
            genres = ID3Editor.after(com, "- ")
            comment_split_by_space = com.split(" ")
            key = comment_split_by_space[0]
            energy = comment_split_by_space[2]
            comment_split_by_comma = genres.split(", ")

            categories = []
            for item in comment_split_by_comma:
                categories.append(item)

        return categories, key, energy

    def id3_write(path, string):
        audiofile = eyed3.load(path)
        audiofile.tag.comments.set(string)
        audiofile.tag.save()

    def get_details(path):
        audiofile = eyed3.load(path)
        title = audiofile.tag.title
        artist = audiofile.tag.artist
        return title, artist


if __name__ == '__main__':
    playlist_name = "90s"
    itunes_xml = "C:/Users/Daniel/Music/iTunes/iTunes Music Library.xml"
    excel_file = 'Genre.xlsx'
    path_list = playlist_list(playlist_name, itunes_xml)
    for item in path_list:
        audio_path = item
        app.main(excel_file, audio_path)
