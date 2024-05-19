import sys
import os
import re
import glob
import csv
from picoq import PICoq

default_path_to_vfiles ="/home/kenkuga/Documents/Coq/coq-8.15.2/theories/*/*.v" # "./coq-8.13.2/theories/*/*.v"

default_path_to_data_csv_file = "./data.csv"

############### data_utils.py
### import sys, os, glob
# sys.path.append("../picoq")
# from picoq import *
# from picoq.picoq 

# dirlist is a list of "path to directory" 
# (possibly) containing .v files 
#  or whose subdirectories (possibly) contain .v files "
def get_vfile_paths(dirlist):
    vfilelislis = []
    for d in dirlist:
        vfilelislis.append(glob.glob(d+"/**/*.v", recursive=True))
    vfilelist = [p for lis in vfilelislis for p in lis] # flatten
    return vfilelist

# with open("file_of_dirpaths", 'r') as infile:
#   with open("file_of_vfilepaths", "w") as outfile:
def vpathsfile_from_dpathsfile(outfile, infile):
    dlis = infile.readlines()
    dirlist = [s.strip() for s in dlis]
    vflist = get_vfile_paths(dirlist)
    for vf in vflist:
        outfile.write("%s\n" %vf)


##############

def remove_comments(code: str) -> str:
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

def clean_codes(s: str) -> list:
    s = remove_comments(s)
    s = re.sub(r"\s+", " ", s, flags=re.DOTALL)
    codes = re.split(r"\.\s+", s)
    return [code+"." for code in codes if code !='']


def coq_to_data(coq_files=default_path_to_vfiles,
                data_file=default_path_to_data_csv_file):
    """ coq_files : paths to coq .v files, e.g., "~/coq-8.13.2/theories/*/*.v" 
        data_file : target csv file whrer data will be added. 
    """

    vfiles = glob.glob(coq_files)
    dfile =  open(data_file, 'a', newline='')
    writer = csv.writer(dfile, quoting=csv.QUOTE_ALL)

    coq =  PICoq()
    
    for vfile in vfiles:
        with open(vfile, 'r', encoding='utf-8') as f:
            data = []
            codes = clean_codes(f.read())
            proof_dgm = ""
            tactics =""
            for code in codes:
                rdict = coq.enter(code)
                if rdict['proof_status'] == 'NOT_IN_PROOF':
                    continue
                elif rdict['proof_status'] == 'GOAL_UPDATED':
                    if proof_dgm != "":
                        data.append([proof_dgm, tactics + " " + code])
                    proof_dgm = rdict['proof_dgm']
                    tactics = ""
                elif rdict['proof_status'] == 'PROVING':
                    tactics = tactics + " " + code
                elif rdict['proof_status'] == 'NO_MORE_GOALS':
                    data.append( [proof_dgm, tactics + " " + code])
                    proof_dgm = ""
                    tactics = ""
                else:
                    continue
            writer.writerows(data)
            dfile.flush()
            os.fsync(dfile.fileno())
            print("\n###################################################\n")
            num_data = len(data)
            print(f"data contains {num_data} pairs.\n")
            #print(data)
            print("###################################################\n\n")
   
    coq.close()

    dfile.close()


        
if __name__ == "__main__":
    coq_to_data()
## data_utils.py
""" import sys, os, glob

# sys.path.append("../picoq")
# from picoq import *
# from picoq.picoq 

# dirlist is a list of "path to directory" 
# (possibly) containing .v files 
#  or whose subdirectories (possibly) contain .v files "
def get_vfile_paths(dirlist):
    vfilelislis = []
    for d in dirlist:
        vfilelislis.append(glob.glob(d+"/**/*.v", recursive=True))
    vfilelist = [p for lis in vfilelislis for p in lis] # flatten
    return vfilelist

# with open("file_of_dirpaths", 'r') as infile:
#   with open("file_of_vfilepaths", "w") as outfile:
def vpathsfile_from_dpathsfile(outfile, infile):
    dlis = infile.readlines()
    dirlist = [s.strip() for s in dlis]
    vflist = get_vfile_paths(dirlist)
    for vf in vflist:
        outfile.write("%s\n" %vf)

def get_theorem_proof_pairs(vfile):
"""
