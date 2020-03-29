from tkinter import *

from excel_import import ExcelImport


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


if __name__ == '__main__':

    input_file = 'Genre.xlsx'
    data = ExcelImport(input_file)
    input_array = data.array()
    input_ncd = data.ncd
    root = Tk()
    fm = Frame(root)
    root.title("DJ library editor")

    for item in input_ncd:
        Button(fm, text=item).pack(side=TOP, anchor=W, fill=X, expand=YES)

    fm.pack(side=LEFT, fill=BOTH, expand=YES)
    fm2 = Frame(root)

    for item in input_array:
        line = Checkbar(fm2, item)
        line.pack(side=TOP, anchor=W, fill=X, expand=YES)
        line.config(relief=GROOVE, bd=1)

    fm2.pack(side=LEFT, padx=10)


    def allstates():
        print(list(input_array.state()))


    Button(root, text='Quit', command=root.quit).pack(side=RIGHT)
    Button(root, text='Peek', command=allstates).pack(side=RIGHT)
    root.mainloop()
