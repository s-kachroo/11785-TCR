import torch
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import pandas as pd


class PytdcDatasetTriplet(Dataset):
    def __init__(self, dataframe, configs):
        """
        Initializes the dataset object.
        :param dataframe: A DataFrame containing the data to be used in this dataset.
        """
        self.configs = configs

        # Using specific columns for features and labels
        TCR = dataframe['tcr'].values
        epitope = dataframe['epitope_aa'].values
        label = dataframe['label'].values

        # Storing TCR and epitope based on label
        self.TCR = TCR[label == 1]
        self.epitope = epitope[label == 1]

        self.TCR_neg = TCR[label != 1]
        self.epitope_neg = epitope[label != 1]
    def __len__(self):
        """
        Returns the number of samples in the dataset.
        """
        return len(self.epitope)

    def __getitem__(self, idx):
        """
        Retrieves the feature tensor and label tensor at the specified index.
        :param idx: Index of the data point to retrieve.
        :return: A tuple containing the feature tensor and label tensor.
        """
        return self.TCR[idx], self.epitope[idx]


def get_dataloader(configs):
    if configs.dataset == "pytdc":
        # Load validation and test data
        valid_data = pd.read_csv(f'./dataset/pytdc/valid_PyTDC.csv')
        # test_data = pd.read_csv(f'./dataset/pytdc/test_PyTDC.csv')

        train_data = pd.read_csv(f'./dataset/pytdc/train_PyTDC.csv')

        # Create datasets
        if configs.contrastive_mode == "Triplet":
            train_dataset = PytdcDatasetTriplet(train_data, configs)
            valid_dataset = PytdcDatasetTriplet(valid_data, configs)
        else:
            raise ValueError("Wrong contrastive mode specified.")
        # test_dataset = pytdcDataset(test_data, configs)

        # Create dataloaders
        train_loader = DataLoader(train_dataset, batch_size=configs.batch_size, shuffle=True, drop_last=True)
        valid_loader = DataLoader(valid_dataset, batch_size=configs.batch_size, shuffle=False)
        # test_loader = DataLoader(test_dataset, batch_size=configs.batch_size, shuffle=False)

        # return {'train': train_loader, 'valid': valid_loader, 'test': test_loader}
        return {'train': train_loader, 'valid': valid_loader}
    else:
        raise ValueError("Wrong dataset specified.")
