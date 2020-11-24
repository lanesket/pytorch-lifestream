import logging

import pandas as pd
from torch.utils.data import ChainDataset
from torch.utils.data.dataloader import DataLoader

import pytorch_lightning as pl

from dltranz.data_load import IterableChain, padded_collate, IterableAugmentations
from dltranz.data_load.augmentations.seq_len_limit import SeqLenLimit
from dltranz.data_load.iterable_processing.feature_filter import FeatureFilter
from dltranz.data_load.iterable_processing.target_extractor import TargetExtractor
from dltranz.data_load.parquet_dataset import ParquetDataset, ParquetFiles
from dltranz.metric_learn.inference_tools import save_scores
from dltranz.seq_mel import SequenceMetricLearning
from dltranz.train import score_model
from dltranz.util import get_conf

logger = logging.getLogger(__name__)


def create_inference_dataloader(conf):
    """This is inference dataloader for `experiments`
    """
    post_processing = IterableChain(
        TargetExtractor(target_col=conf['col_id']),
        FeatureFilter(drop_non_iterable=True),
        IterableAugmentations(
            SeqLenLimit(**conf['SeqLenLimit']),
        )
    )
    l_dataset = [
        ParquetDataset(
            ParquetFiles(path).data_files,
            post_processing=post_processing,
            shuffle_files=False,
        ) for path in conf['dataset_files']]
    dataset = ChainDataset(l_dataset)
    return DataLoader(
        dataset=dataset,
        collate_fn=padded_collate,
        shuffle=False,
        num_workers=conf['loader.num_workers'],
        batch_size=conf['loader.batch_size'],
    )


def main(args=None):
    conf = get_conf(args)

    pl.seed_everything(42)

    model = SequenceMetricLearning(conf['params'])
    model.load_from_checkpoint(conf['model_path'])

    dl = create_inference_dataloader(conf['inference_dataloader'])

    ids, pred = score_model(model, dl, conf['params'])

    df_scores_cols = [f'v{i:003d}' for i in range(pred.shape[1])]
    col_id = conf['inference_dataloader.col_id']
    df_scores = pd.concat([
        pd.DataFrame({col_id: ids}),
        pd.DataFrame(pred, columns=df_scores_cols),
        ], axis=1)
    logger.info(f'df_scores examples: {df_scores.shape}:')

    save_scores(df_scores, None, conf['output'])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-7s %(funcName)-20s   : %(message)s')
    logging.getLogger("lightning").setLevel(logging.INFO)

    main()
