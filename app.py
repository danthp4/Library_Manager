import old
from tkinter.filedialog import askopenfilename

if __name__ == '__main__':
    audio_path = askopenfilename()
    excel_file = 'Genre.xlsx'
    old.main(audio_path, excel_file)
