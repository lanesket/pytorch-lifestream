from fastai.tabular import *
import pandas as pd
import numpy as np
import os

def train(X_train, y_train, X_valid, y_valid):
    data = to_fastai_data(X_train, y_train, X_valid, y_valid)

    learn = tabular_learner(data, layers=[200,100], metrics=accuracy)
    learn.fit_one_cycle(10, 1e-2)
    return 0.56

def train_from_config(X_train, y_train, X_valid, y_valid, config):
    pass


def to_fastai_data(X_train, y_train, X_valid, y_valid):
    data = np.concatenate((
                    np.concatenate((X_train, y_train.reshape(-1, 1)), axis=1),
                    np.concatenate((X_valid, y_valid.reshape(-1, 1)), axis=1)
                    ), axis=0)
    cols = [f'col_{i}' for i in range(data.shape[-1])]
    cols[-1] = 'target'
    df = pd.DataFrame(data=data, columns=cols)

    # train test split
    len_test = y_valid.shape[0]
    len_train = y_train.shape[0]
    valid_idx = range(len_train, len_train + len_test)

    preprocess = []
    target = 'target'
    cat_vars = []
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    return TabularDataBunch.from_df(path, df, target, valid_idx=valid_idx, procs=preprocess, cat_names=cat_vars)


'''train(np.random.randn(10000, 5), 
      np.random.randint(0, 2, (10000,)),
      np.random.randn(1000, 5), 
      np.random.randint(0, 2, (1000,))
      )'''