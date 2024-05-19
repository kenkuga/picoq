import sys, os, glob
import re
import csv

# from typing_extensions import dataclass_transform
import pandas as pd

R_Q_option_pat = re.compile(r"^\s*-[RQ] (.+?) (.+?)$")
v_file_pat = re.compile(r"^/s*.+?\.v$")


def read_coqprojects(coqproj_paths_file: str) -> list:
    projlist = []
    with open(coqproj_paths_file, "r") as cppf:
        proj_paths = cppf.readlines()
        for path in proj_paths:
            path = path.strip()
            if path[-1] == "/":
                path = path[:-1]
            original_dir = os.getcwd()
            os.chdir(path)
            proj = [path]
            R_Q_ops = ""
            v_files = []
            if os.path.isfile("_CoqProject"):
                with open("./_CoqProject") as cp:
                    cp_list = cp.readlines()
                    for line in cp_list:
                        line = line.strip()
                        R_Q_match = R_Q_option_pat.match(line)
                        v_match = v_file_pat.match(line)
                        if R_Q_match:
                            R_Q_ops = R_Q_ops + " " + R_Q_match.group(0)
                        if v_match:
                            v_files = v_files.append(v_match.group(0))
            if len(v_files) == 0:
                v_files = glob.glob(path + "/**/*.v", recursive=True)
                print(f"No -R or -Q options in {path}")
            proj.append(R_Q_ops)
            proj.append(v_files)
            projlist.append(proj)
            os.chdir(original_dir)
    return projlist  # [ ["path_to_project", "-R or -Q options", ["file1.v", "file2.v, ..."]], ...]


def remove_comments(code):
    characters = []
    num_left = 0
    in_string = False
    i = 0
    while i < len(code) - 1:
        if code[i] == '"':
            in_string = not in_string
        if not in_string and code[i : i + 2] == "(*":
            num_left += 1
            i += 2
        elif not in_string and num_left > 0 and code[i : i + 2] == "*)":
            num_left -= 1
            i += 2
        elif num_left == 0:
            characters.append(code[i])
            i += 1
        else:
            i += 1
    characters.append(code[-1])
    code_without_comment = "".join(characters)
    return code_without_comment


def normalize_spaces(s):
    return re.sub(r"\s+", " ", s, flags=re.DOTALL)


def separate_commands(code_string):
    code_string = remove_comments(code_string) + " "
    code_string = re.sub(r"\s+", " ", code_string)
    code_string = re.sub(r"^ ", "", code_string)
    commands = re.split(r"\. ", code_string)
    return [cmd + "." for cmd in commands if cmd != ""]


def tokenizer_training_generator_from_corpus(df_or_csv):
    '''
    :parameter df_or_csv: training corpus of either
    pandas.DataFrame with two columns"source_text", "target_text" or
    path to csv file with two columns
    :return: generator for combined strings for training tokenizers
    '''
    if type(df_or_csv) == str: # path to csv file
        df = pd.read_csv(df_or_csv, names=("source_text", "target_text"))
    else: # pd.DataFrame
        df = df_or_csv
    df1 = df.assign(source_text = df.source_text.astype(str) + ", "\
         + df.target_text.astype(str))
    df2 = df1.fillna("")
    for i in range(0, len(df2), 1000):
        samples = df2[i:i+1000]
        yield samples["source_text"]

from transformers import AutoTokenizer

def tokenizer_train_new(model_name, gen_corpus, save_name='tokenizer', num=52000):
    '''
    :parameter model_name: HuggingFace model 
    't5-small', 't5-base', 't5-large', ...,'gpt2',...
    :parameter gen_corpus: iterator or generator for corpus
    :paremeter save_name: path to the directory for the new tokenizer  
    :return: new tokenizer
    '''
    old_tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer = old_tokenizer.train_new_from_iterator(gen_corpus, num)
    tokenizer.save_pretrained(model_name + '_' + save_name)
    return tokenizer

    