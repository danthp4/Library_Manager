from tkinter import *

from excel_import import ExcelImport
from player import play


class Checkbar(Frame):
    def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
        Frame.__init__(self, parent)
        self.vars = []
        for pick in picks:
            var = IntVar()
            chk = Checkbutton(self, text=pick, variable=var)
            chk.pack(side=side, anchor=anchor, expand=YES)
            self.vars.append(var)

    def state(self):
        return map((lambda var: var.get()), self.vars)


def main(audio_file, excel_file):
    audio_path = audio_file
    input_file = excel_file
    data = ExcelImport(input_file)
    main.input_array = data.array()
    main.input_ncd = data.ncd
    root = Tk()
    root.title("DJ library editor")

    fm = Frame(root)
    for item in main.input_ncd:
        Label(fm, text=item, relief=GROOVE, bd=5).pack(side=TOP, anchor=W, fill=X)

    fm.pack(side=LEFT, padx=10)
    fm2 = Frame(root)
    main.dict = {}
    i = 0
    for item in main.input_array:
        main.dict[main.input_ncd[i]] = Checkbar(root, item)
        main.dict[main.input_ncd[i]].pack(side=TOP, anchor=W, fill=X)
        main.dict[main.input_ncd[i]].config(relief=GROOVE, bd=1)
        i += 1

    fm2.pack(side=LEFT, padx=10)

    fm3 = Frame(root)
    Button(fm3, text='Quit', command=root.quit).pack(side=RIGHT)
    Button(fm3, text='Peek', command=allstates).pack(side=RIGHT)
    Button(fm3, text="Play", command=lambda: play(audio_path)).pack(side=RIGHT)
    fm3.pack(side=RIGHT, padx=10)

    root.mainloop()


def allstates():
    for i in range(len(main.input_ncd)):
        x = main.dict.get(main.input_ncd[i])
        print(str(main.input_ncd[i]), list(x.state()))

if __name__ == '__main__':
    main()