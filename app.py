import gui
from tkinter.filedialog import askopenfilename

if __name__ == '__main__':
    audio_path = askopenfilename()
    excel_file = 'Genre.xlsx'
    gui.main(audio_path, excel_file)
