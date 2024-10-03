import torch
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import pandas as pd


class pytdcDataset(Dataset):
    def __init__(self, dataframe):
        """
        Initializes the dataset object.
        :param dataframe: A DataFrame containing the data to be used in this dataset.
        """
        # Using specific columns for features and labels
        self.TCR = dataframe['tcr'].values
        self.epitope = dataframe['epitope_aa'].values

    def __len__(self):
        """
        Returns the number of samples in the dataset.
        """
        return len(self.peptide)

    def __getitem__(self, idx):
        """
        Retrieves the feature tensor and label tensor at the specified index.
        :param idx: Index of the data point to retrieve.
        :return: A tuple containing the feature tensor and label tensor.
        """
        return self.peptide[idx], self.binding_TCR[idx]


def get_dataloader(configs):
    if configs.dataset == "pytdc":
        # Load validation and test data
        valid_data = pd.read_csv(f'./dataset/pytdc/valid_PyTDC.csv')
        test_data = pd.read_csv(f'./dataset/pytdc/test_PyTDC.csv')

        # Combine and shuffle remaining data for training
        train_data = pd.read_csv(f'./dataset/pytdc/train_PyTDC.csv')

        # Create datasets
        train_dataset = pytdcDataset(train_data)
        valid_dataset = pytdcDataset(valid_data)
        test_dataset = pytdcDataset(test_data)

        # Create dataloaders
        train_loader = DataLoader(train_dataset, batch_size=configs.batch_size, shuffle=True, drop_last=True)
        valid_loader = DataLoader(valid_dataset, batch_size=configs.batch_size, shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size=configs.batch_size, shuffle=False)

        return {'train': train_loader, 'valid': valid_loader, 'test': test_loader}
    else:
        raise ValueError("Wrong dataset specified.")
