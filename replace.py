import copy, replace
from tkinter import *
from excel_import import ExcelImport
from itunes import playlist_list
from player import play, stop
from ID3_Manager import ID3Editor


class Checkbar(Frame):
   def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
      Frame.__init__(self, parent)
      self.vars = []
      for pick in picks:
         var = IntVar()
         chk = Checkbutton(self, text=pick, variable=var)
         chk.select()
         chk.pack(side=side, anchor=anchor, expand=YES)
         self.vars.append(var)
   def state(self):
      return map((lambda var: var.get()), self.vars)





def close_inst(audio_path):
    # stop audio and write to file on close
    stop(audio_path)
    additional_collector()
    write()
    main.root.destroy()


def disable_event():
    # for stopping accidental close via window x
    pass

def allstates():
    # To get state output as list un-comment below
    for i in range(len(main.input_ncd)):
        x = main.dict.get(main.input_ncd[i])
        print(str(main.input_ncd[i]), list(x.state()))
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

def main(excel_file, audio_path):
    # initialise variables
    main.audio_path = audio_path
    input_file = excel_file
    data = ExcelImport(input_file)
    main.input_array = data.array()
    data.ncd.append('Uncategorised')
    main.input_ncd = data.ncd
    main.dict = {}

    # tkinkter window options
    main.root = Tk()
    main.root.protocol("WM_DELETE_WINDOW", disable_event)
    main.root.title("DJ library editor - Replace function")

    # get details from ID3 for audio file
    id3_output = ID3Editor.main_id3(audio_path)
    main.cat = id3_output[0]
    main.key = id3_output[1]
    main.energy = id3_output[2]
    details = ID3Editor.get_details(audio_path)
    song_title = details[0]
    artist = details[1]

    # initalise string update in window
    main.update = StringVar()

    # draw labels
    fm = Frame(main.root)
    for item in main.input_ncd:
        Label(fm, text=item, relief=GROOVE, bd=5).pack(side=TOP, anchor=W, fill=X)
    fm.pack(side=LEFT, padx=10)

    # draw checkboxes
    fm2 = Frame(main.root)
    i = 0
    for item in main.input_array:
        main.dict[main.input_ncd[i]] = Checkbar(fm2, item)
        main.dict[main.input_ncd[i]].pack(side=TOP, anchor=W, fill=X)
        main.dict[main.input_ncd[i]].config(relief=GROOVE, bd=1)
        i += 1
    fm2.pack(side=LEFT, padx=10)

    # update string representation
    allstates()

    # draw tkinter
    main.root.mainloop()



if __name__ == '__main__':
    playlist_name = "Replace"
    itunes_xml = "C:/Users/danie/Music/iTunes/iTunes Music Library.xml"
    excel_file = 'Genre.xlsx'
    path_list = playlist_list(playlist_name, itunes_xml)
    for item in path_list:
        audio_path = item
        replace.main(excel_file, audio_path)
