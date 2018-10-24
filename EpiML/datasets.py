import os
import pandas as pd

from EpiML import app


class MiRNA2Disease():
    dir = app.config['MIR2DISEASE_DIR']
    all_entries_file = os.path.join(dir, 'AllEntries.txt')
    disease_list_file = os.path.join(dir, 'diseaseList.txt')
    miRNA_list_file = os.path.join(dir, 'miRNAlist.txt')
    miRNA_target_file = os.path.join(dir, 'miRtar.txt')

    def __init__(self):
        # load miRNA2Disease data
        self.all_entries = pd.read_csv(self.all_entries_file, sep='\t', header=None,
                                       names=['miRNA', 'Disease', 'Up/down regulated', 'Verification', 'Year',
                                              'Reference'])
        self.disease_list = pd.read_csv(self.disease_list_file, sep='\t', header=0)
        self.miRNA_target = pd.read_csv(self.miRNA_target_file, sep='\t', header=0, skiprows=2)


class MiRBase():
    dir = app.config['MIR2BASE_DIR']
    miRBase_xls = os.path.join(dir, 'miRNA.xls')
    id2accession = {}

    def __init__(self):
        # load miRNA2Disease data
        self.miRBase_database = pd.read_excel(self.miRBase_xls)

        for index, row in self.miRBase_database.iterrows():
            self.id2accession[row['ID']] = row['Accession']

    def get_accession(self, id):
        return self.id2accession[id]
