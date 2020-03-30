from tkinter import *
from tkinter.filedialog import askopenfilename

class Checker:
    def loadFile(self):
        self.filename = askopenfilename(filetypes=(("info", "*.xlsx"), ("all file", "*.*")))
        self.filedir.delete(0, "end")
        self.filedir.insert(0, self.filename)

    def __init__(self, master):
        master.title("Checker")

        self.load_button = Button(master, text="load file", command=self.loadFile)
        self.load_button.grid(row=0, column=0)
        self.filedir = Entry(master, text=" ")
        self.filedir.grid(row=0, column=1)

if __name__=='__main__':
    root = Tk()
    k = Checker(root)
    root.mainloop()