import sys, os
import re, glob
import csv
from typing_extensions import dataclass_transform
from picoq2 import PICoq
import pandas as pd

import torch
import numpy as np
from transformers import AutoTokenizer, AutoConfig
from transformers import T5ForConditionalGeneration
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelWithLMHead
import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from pytorch_lightning.callbacks.progress import TQDMProgressBar
import t5model_from_tokenizer
from t5model_from_tokenizer import T5_from_tokenizer


import utils
from utils import separate_commands
from sklearn.model_selection import train_test_split
import simplet5a
from simplet5a import SimpleT5

import pdb


# !pip install --upgrade sentencepiece : required for simplet5
# !pip install --upgrade simplet5 required. 
# above commnand could automatically downgrade transformers as  
# simplet5 0.1.4 requires transformers==4.16.2 

csvdatapath = "/content/drive/MyDrive/Hawaii20220826/coq_theorem_proof_data.csv"
            
## EXAMPLE OF OUTPUTS 
# simplet5-epoch-0-train-loss-2.1575-val-loss-1.3964
# simplet5-epoch-1-train-loss-1.4169-val-loss-1.1179
# simplet5-epoch-2-train-loss-1.1767-val-loss-0.9725
# simplet5-epoch-3-train-loss-1.0157-val-loss-0.8825
# simplet5-epoch-4-train-loss-0.8944-val-loss-0.8247
CHECKOUT_DATA = "outputs/simplet5-epoch-4-train-loss-0.8944-val-loss-0.8247"

class T5Coq(PICoq):
    def __init__(
        self,           
        coq_excutable="coqtop -emacs",
        timeout=10,
        maxread=10000,
        echo=False,
        encoding="utf-8",
        codec_errors="strict"
    ):  
        self.t5 = None
        self.train_df = None
        self.eval_df = None
        self.prediction_list = []

        super(T5Coq, self).__init__(
            executable=coq_excutable,
            timeout=timeout,
            maxread=maxread,
            echo=echo,
            encoding=encoding,
            codec_errors=codec_errors,
        )

    def set_t5(self, model_name, t5_tokenizer_dir) -> None:
        """ Set SimpleT5 model from tokenizer
        :parameter model_name:  t5-small, t5-base, t5-large
        :parameter t5_tokenizer_dir: path to saved tokenizer directory
        """
        self.t5 = SimpleT5()
        self.t5.set_t5(model_name, t5_tokenizer_dir)

    def set_t5_pretrained(self, model_type="t5", model_name="t5-base"):
        self.t5 = simpletT5()
        self.t5.from_pretrained(model_type, model_name)
        
    
    def load_model(self, data=CHECKOUT_DATA, use_gpu=False):
        self.model.load_model("t5", data, use_gpu=use_gpu)

    def set_train_data_from_csv(self, data_csv, test_size=0.2):
        data_df = pd.read_csv(data_csv)
        data_df.columns = ["source_text", "target_text"]
        data_df['source_text'] = "prove_in_coq: " + data_df['source_text']
        self.train_df, self.eval_df = train_test_split(data_df, test_size)


    def train_model(self, 
            train_df=None, # pandas dataframe with 2 columns: source_text & target_text
            eval_df=None, # pandas dataframe with 2 columns: source_text & target_text
            source_max_token_len = 512, 
            target_max_token_len = 128,
            batch_size = 8,
            max_epochs = 5,
            use_gpu = True,
            outputdir = "outputs",
            early_stopping_patience_epochs = 0,
            precision = 32
            ):
        if train_df!=None: self.train_df = train_df
        if eval_df != None: self.eval_df = eval_df
            
        self.model.train(
            self.train_df, 
            self.eval_df,
            source_max_token_len = source_max_token_len, 
            target_max_token_len = target_max_token_len,
            batch_size = batch_size,
            max_epochs = max_epochs,
            use_gpu = use_gpu,
            outputdir = outputdir,
            early_stopping_patience_epochs = early_stopping_patience_epochs,
            precision = precision
            )

    def enter(self, commands="Check I.", num_prediction=0, prefix="prove in coq"): # commands is a string composed of sentenses i.e. commands.
        responses = super(T5Coq, self).enter(commands) # responses is a list, each entry is a response to each 
        pdb.set_trace() ##########################
        if self.t5 != None:
            self.prediction_list = self.t5.predict(
                prefix+": "+responses[-1]["response"],  # prediction from the last response. 
                num_return_sequences=num_prediction, num_beams=num_prediction+1) 
        return responses, self.prediction_list

    def __call__(self, commands, num_prediction=0):
        return self.enter(commands, num_prediction)
 

    



