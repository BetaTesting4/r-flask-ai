import pandas as pd

# Read the Excel file
excel_file = pd.ExcelFile("data/input.xlsx")
df = pd.read_excel(excel_file)

# Print the DataFrame
print(df)
