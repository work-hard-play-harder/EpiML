import os
import pandas as pd


class miRNA2Disease():
    dir = 'EpiMap/datasets/miR2Disease'
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
