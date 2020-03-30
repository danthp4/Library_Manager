from tkinter import *
from tkinter.filedialog import askopenfilename
import eyed3, gui, copy
from excel_import import ExcelImport
from player import play


class Checkbar(Frame):
    def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
        Frame.__init__(self, parent)
        self.vars = []
        var = IntVar()
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


def main(excel_file, audio_path):
    main.audio_path= audio_path
    input_file = excel_file
    data = ExcelImport(input_file)
    main.input_array = data.array()
    data.ncd.append('Additional')
    main.input_ncd = data.ncd
    root = Tk()
    root.title("DJ library editor")
    id3_output = ID3Editor.main_id3(audio_path)
    main.cat = id3_output[0]
    main.key = id3_output[1]
    main.energy = id3_output[2]
    main.leftover_cat = copy.copy(main.cat)

    fm = Frame(root)
    for item in main.input_ncd:
        Label(fm, text=item, relief=GROOVE, bd=5).pack(side=TOP, anchor=W, fill=X)

    fm.pack(side=LEFT, padx=10)
    fm2 = Frame(root)
    main.dict = {}
    for list in main.input_array:
        for item in list:
            for value in main.cat:
                if value == item:
                    main.leftover_cat.remove(value)
    main.input_array.append(main.leftover_cat)
    i = 0
    for item in main.input_array:
        main.dict[main.input_ncd[i]] = Checkbar(fm2, item)
        main.dict[main.input_ncd[i]].pack(side=TOP, anchor=W, fill=X)
        main.dict[main.input_ncd[i]].config(relief=GROOVE, bd=1)
        i += 1


    fm2.pack(side=LEFT, padx=10)
    fm3 = Frame(root)
    Button(fm3, text='Quit', command=root.quit).pack(side=RIGHT)
    Button(fm3, text='Check states', command=allstates).pack(side=RIGHT)
    Button(fm3, text='Write', command=lambda: write()).pack(side=RIGHT)
    Button(fm3, text="Play", command=lambda: play(audio_path)).pack(side=RIGHT)
    fm3.pack(side=RIGHT, padx=10)

    root.mainloop()


def allstates():

    """for i in range(len(main.input_ncd)):
        x = main.dict.get(main.input_ncd[i])
        print(str(main.input_ncd[i]), list(x.state()))"""

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


def write():

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

        print(key, '-', energy, '-', ', '.join(map(str, comment_split_by_comma)))
        return categories, key, energy

    def id3_write(path, string):
        audiofile = eyed3.load(path)
        audiofile.tag.comments.set(string)
        audiofile.tag.save()


if __name__ == '__main__':
    excel_file = 'Genre.xlsx'
    audio_path = "song_directory/07 Melting Point.mp3"
    a = gui.main(excel_file, audio_path)
