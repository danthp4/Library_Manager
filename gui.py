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
        Label(fm, text=item, relief="groove", bd=5).pack(side=TOP, anchor=W, fill=X, expand=YES)

    fm.pack(side=LEFT, padx=10)
    fm2 = Frame(root)
    list ="global"
    list=[]
    i = 0
    for item in input_array:
        list.append(str(i))
        list[i] = Checkbar(root, item)
        list[i].pack(side=TOP, anchor=W, fill=X, expand=YES)
        list[i].config(relief=GROOVE, bd=1)
        i =+ 1



    fm2.pack(side=LEFT, padx=10)



    def allstates():
        print(list[0])
        print(list[0].state)
        print(list[list[0].state()])


    Button(root, text='Quit', command=root.quit).pack(side=RIGHT)
    Button(root, text='Peek', command=allstates).pack(side=RIGHT)
    root.mainloop()
