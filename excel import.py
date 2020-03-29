import pandas as pd

data = pd.read_excel (r'Genre.xlsx')
num_col_data=list(data)
array = []
i = 0
for column in num_col_data:
    col = data.iloc[:, i].tolist()
    array.append(col)
    i += 1

print(array)