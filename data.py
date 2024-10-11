import torch
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import pandas as pd
import random


class PytdcDatasetTriplet(Dataset):
    def __init__(self, dataframe, configs):
        """

        """
        self.configs = configs

        # Using specific columns for features and labels
        TCR = dataframe['tcr'].values
        epitope = dataframe['epitope_aa'].values
        label = dataframe['label'].values

        # Storing TCR and epitopes based on label, these are positive pairs
        self.TCR = TCR[label == 1]
        self.epitope = epitope[label == 1]

        # These are negative pairs in the original dataset
        self.TCR_neg = TCR[label != 1]
        self.epitope_neg = epitope[label != 1]

        # Generate dictionaries mapping TCR to all related epitopes and vice versa
        self.TCR_epitope = {}
        self.epitope_TCR = {}

        for tcr, epi in zip(self.TCR, self.epitope):
            if tcr not in self.TCR_epitope:
                self.TCR_epitope[tcr] = []
            self.TCR_epitope[tcr].append(epi)

            if epi not in self.epitope_TCR:
                self.epitope_TCR[epi] = []
            self.epitope_TCR[epi].append(tcr)

        # Negative sampling dictionaries
        self.TCR_epitope_neg = {}
        self.epitope_TCR_neg = {}

        for tcr, epi_neg in zip(self.TCR, self.epitope_neg):
            if tcr not in self.TCR_epitope_neg:
                self.TCR_epitope_neg[tcr] = []
            self.TCR_epitope_neg[tcr].append(epi_neg)

        for epi, tcr_neg in zip(self.epitope, self.TCR_neg):
            if epi not in self.epitope_TCR_neg:
                self.epitope_TCR_neg[epi] = []
            self.epitope_TCR_neg[epi].append(tcr_neg)

        self.full_list = []
        for ep in self.epitope_TCR.keys():
            self.full_list.append(ep)
    def __len__(self):
        """

        """
        return len(self.full_list)

    def __getitem__(self, idx):
        """

        """
        anchor_epitope = self.full_list[idx]
        anchor_TCR = random.choice(self.epitope_TCR[anchor_epitope])
        positive_TCR = NotImplementedError
        negative_TCR = NotImplementedError
        return {'anchor_TCR': anchor_TCR, 'positive_TCR': positive_TCR, 'negative_TCR': negative_TCR}


def get_dataloader(configs):
    if configs.dataset == "pytdc":
        train_data = pd.read_csv(f'./dataset/pytdc/train_PyTDC.csv')
        valid_data = pd.read_csv(f'./dataset/pytdc/valid_PyTDC.csv')
        if configs.contrastive_mode == "Triplet":
            train_dataset = PytdcDatasetTriplet(train_data, configs)
            valid_dataset = PytdcDatasetTriplet(valid_data, configs)
            # get
            # get
        else:
            raise ValueError("Wrong contrastive mode specified.")
        train_loader = DataLoader(train_dataset, batch_size=configs.batch_size, shuffle=True, drop_last=True)
        valid_loader = DataLoader(valid_dataset, batch_size=configs.batch_size, shuffle=False)
        return {'train_loader': train_loader, 'valid_loader': valid_loader,
                'epitope_TCR': train_dataset.epitope_TCR, 'TCR_epitope': train_dataset.TCR_epitope,
                'epitope_TCR_neg': train_dataset.epitope_TCR_neg, 'TCR_epitope_neg': train_dataset.TCR_epitope_neg}
    else:
        raise ValueError("Wrong dataset specified.")
