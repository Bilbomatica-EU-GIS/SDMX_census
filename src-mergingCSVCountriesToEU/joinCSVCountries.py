import csv
import glob

path = './INPUT'
allFiles = glob.glob(path + "/*.csv")
df_out_filename = './OUTPUT/CENSUS_GRID_N_EU_2021_0000_V0001.csv'
write_headers = True
with open(df_out_filename, 'w', newline='', encoding='utf-8') as fout:
    writer = csv.writer(fout, delimiter=';')
    for filename in allFiles:
        with open(filename) as fin:
            reader = csv.reader(fin, delimiter=';')
            headers = next(reader)
            numberOfColumns = 0
            if (len(headers) > 0):
                numberOfColumns_header = headers[0].count(';')
            if write_headers:
                write_headers = False  # Only write headers once
                writer.writerow(headers)
            for row in reader:
                numberOfColumns_row = 0
                if (len(row) > 0):
                    numberOfColumns_row = row[0].count(';')
                if (numberOfColumns_header == numberOfColumns_row):
                    row[-2] = 'EU'
                    writer.writerow(row)  # Write all remaining rows
            print(filename + " has been merged.")

print("Finish merging countries")