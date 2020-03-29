import pandas as pd


class ExcelImport:
    def __init__(self, path):
        self.path = path
        data = pd.read_excel(path)
        self.input = data
        num_col_data = list(data)
        print(num_col_data)
        self.ncd = num_col_data
        array = []
        i = 0
        for column in num_col_data:
            col = data.iloc[:, i].tolist()
            col = [x for x in col if str(x) != 'nan']
            array.append(col)
            i += 1
        self.output = array


    def array(self):
        return self.output


    def ncd(self):
        return self.ncd
