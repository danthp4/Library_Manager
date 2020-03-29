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
    root.title("DJ library editor")

    fm = Frame(root)
    for item in input_ncd:
        Label(fm, text=item, relief="groove", bd=5).pack(side=TOP, anchor=W, fill=X, expand=YES)

    fm.pack(side=LEFT, padx=10)
    fm2 = Frame(root)
    dict = "global"
    dict = {}
    i = 0
    for item in input_array:
        dict[input_ncd[i]] = Checkbar(root, item)
        dict[input_ncd[i]].pack(side=TOP, anchor=W, fill=X, expand=YES)
        dict[input_ncd[i]].config(relief=GROOVE, bd=1)
        i += 1

    fm2.pack(side=LEFT, padx=10)


    def allstates():
        for i in range(len(input_ncd)):
            x = dict.get(input_ncd[i])
            print(str(input_ncd[i]), list(x.state()))



    Button(root, text='Quit', command=root.quit).pack(side=RIGHT)
    Button(root, text='Peek', command=allstates).pack(side=RIGHT)
    root.mainloop()
