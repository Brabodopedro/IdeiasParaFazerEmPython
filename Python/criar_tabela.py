import pandas as pd

# Creating the data for the spreadsheet
data = {
    "Modelo": ["iPhone 13", "iPhone 12", "iPhone 13 Pro", "iPhone 11"],
    "Preço": [5000, 4000, 6000, 3000],
    "Condição": ["Novo", "Usado", "Novo", "Usado"]
}

# Creating a DataFrame
df = pd.DataFrame(data)

# Saving the DataFrame to an Excel file
file_path = "/mnt/data/iPhone_Models.xlsx"
df.to_excel(file_path, index=False)

file_path