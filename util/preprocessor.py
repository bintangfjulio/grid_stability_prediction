import torch
import multiprocessing
import pandas as pd
import pytorch_lightning as pl

from sklearn.model_selection import train_test_split
from scipy.stats import zscore
from imblearn.over_sampling import SMOTE
from torch.utils.data import TensorDataset, DataLoader

class Preprocessor(pl.LightningDataModule):
    def __init__(self, batch_size):
        super(Preprocessor, self).__init__()    
        self.dataset = pd.read_csv('dataset/simulated_electrical_grid.csv')
        self.batch_size = batch_size

    def setup(self, stage=None):
        train_set, valid_set, test_set = self.preprocessor()   
        if stage == "fit":
            self.train_set = train_set
            self.valid_set = valid_set
        elif stage == "test":
            self.test_set = test_set

    def train_dataloader(self):
        return DataLoader(
            dataset=self.train_set,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=multiprocessing.cpu_count()
        )
    
    def val_dataloader(self):
        return DataLoader(
            dataset=self.valid_set,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=multiprocessing.cpu_count()
        )

    def test_dataloader(self):
        return DataLoader(
            dataset=self.test_set,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=multiprocessing.cpu_count()
        )

    def preprocessor(self):
        if os.path.exists("dataset/train_set.pt") and os.path.exists("dataset/valid_set.pt") and os.path.exists("dataset/test_set.pt"):
            print("\nLoading Data...")
            train_set = torch.load("dataset/train_set.pt")
            valid_set = torch.load("dataset/valid_set.pt")
            test_set = torch.load("dataset/test_set.pt")
            print('[ Loading Completed ]\n')
        else:
            print("\nPreprocessing Data...")
            train_set, valid_set, test_set = self.preprocessing_data(self.dataset)
            print('[ Preprocessing Completed ]\n')

        return train_set, valid_set, test_set
    
    def preprocessing_data(self, dataset):
        dataset = self.normalization(dataset)
        X_train_res, y_train_res = self.oversampling(dataset)
        y_train_res = self.label_encoding(y_train_res)

        X_train_valid, X_test, y_train_valid, y_test = train_test_split(X_train_res, y_train_res, test_size=0.2, random_state=42)
        X_train, X_valid, y_train, y_valid = train_test_split(X_train_valid, y_train_valid, test_size=0.1, random_state=42)
    
        X_train_tensor = torch.from_numpy(X_train.values).float()
        y_train_tensor = torch.from_numpy(y_train.values.ravel()).float()
        
        X_valid_tensor = torch.from_numpy(X_valid.values).float()
        y_valid_tensor = torch.from_numpy(y_valid.values.ravel()).float()
        
        X_test_tensor = torch.from_numpy(X_test.values).float()
        y_test_tensor = torch.from_numpy(y_test.values.ravel()).float()

        y_train_tensor = y_train_tensor.unsqueeze(1)
        train_set = TensorDataset(X_train_tensor, y_train_tensor)
        
        y_valid_tensor = y_valid_tensor.unsqueeze(1)
        valid_set = TensorDataset(X_valid_tensor, y_valid_tensor)

        y_test_tensor = y_test_tensor.unsqueeze(1)
        test_set = TensorDataset(X_test_tensor, y_test_tensor)
       
        torch.save(train_set, "dataset/train_set.pt")
        torch.save(valid_set, "dataset/valid_set.pt")
        torch.save(test_set, "dataset/test_set.pt")

        return train_set, valid_set, test_set

    def normalization(self, dataset):
        dataset['tau1 Z'] = zscore(dataset['tau1'])
        dataset['tau2 Z'] = zscore(dataset['tau2'])
        dataset['tau3 Z'] = zscore(dataset['tau3'])
        dataset['tau4 Z'] = zscore(dataset['tau4'])
        dataset['p1 Z'] = zscore(dataset['p1'])
        dataset['p2 Z'] = zscore(dataset['p2'])
        dataset['p3 Z'] = zscore(dataset['p3'])
        dataset['p4 Z'] = zscore(dataset['p4'])
        dataset['g1 Z'] = zscore(dataset['g1'])
        dataset['g2 Z'] = zscore(dataset['g2'])
        dataset['g3 Z'] = zscore(dataset['g3'])
        dataset['g4 Z'] = zscore(dataset['g4'])

        return dataset

    def label_encoding(self, y_train):
        encoder = {'unstable': 0, 'stable': 1}
        y_train = y_train.astype('str').map(encoder)

        return y_train

    def oversampling(self, dataset):
        X = dataset.drop(['tau1','tau2','tau3','tau4','p1', 'p2', 'p3', 'p4','g1','g2','g3','g4','stab','stabf'], axis=1)
        y = dataset['stabf']     
        oversampling = SMOTE(random_state=42)
        X_train, y_train = oversampling.fit_resample(X, y)

        return X_train, y_train
