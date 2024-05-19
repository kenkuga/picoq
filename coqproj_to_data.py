from cgi import print_form
from http.client import RemoteDisconnected
import sys, os
import re, glob, pathlib
import csv
from typing_extensions import dataclass_transform
from picoq2 import PICoq
from utils import separate_commands
import pandas as pd
from tqdm import tqdm
import pdb

PATH_TO_DATA_CSV = "./data.csv"

IRQ_option_pat = re.compile(r"^\s*-[IRQ] (.+?)$")
v_file_pat = re.compile(r"^\s*[^#].+?\.v$") # '#' for comment-out


def projpaths_to_projlist(coqproj_pathfile: str) -> list:
    """
    :param coqproj_pathfile: txt file with each line
      showing a path_to_project_dir (_CoqProject directory if any) 
    :return: projlist
      [ ["path_to_project", "-R, -Q options", ["file1.v", "file2.v, ..."]], ...]
    """
    projlist = []
    
    with open(coqproj_pathfile, "r") as cppf:
        proj_paths = cppf.readlines()
        for path in proj_paths:
            path = path.strip()
            if path[-1] == "/":
                path = path[:-1]
            pwd = os.getcwd()
            os.chdir(path)
            proj = [path]
            IRQ_ops = ""
            v_files = []
            cproj = ""

            if os.path.isfile("_CoqProject"):
                cproj = "./_CoqProject"
            elif os.path.isfile("Make"):
                cproj = "./Make"  
            elif os.path.isfile("_CoqConfig"):
                cproj = "./_CoqConfig"  # possibly old: check compatibility
            
            if cproj != "":
                with open(cproj) as cp:
                    cp_list = cp.readlines()
                    for line in cp_list:
                        line = line.strip()
                        IRQ_match = IRQ_option_pat.match(line)
                        vmatch = v_file_pat.match(line)
                        if IRQ_match:
                            IRQ_ops = IRQ_ops + " " + IRQ_match.group(0)
                        if vmatch:
                            v_files.append(line)
            if len(v_files) == 0:
                v_files = glob.glob(path + "/**/*.v", recursive=True)
            proj.append(IRQ_ops)
            proj.append(v_files)
            projlist.append(proj)
            os.chdir(pwd)
    
    return projlist  


def vfiles_to_rawdata(vfile_list, proj_dir="", coq_options="", printall=False): 
    """
    returns list of output dicts from coqtop executed on .v files in vfile_list
    
    :param vfile_list: a list of vfilepaths relative to proj_dir
    :param proj_dir: typically the _CoqProject directory
    :param coq_options: coqtop options, -R and -Q options specified in _CoqProject
    :param printall: False(Default)/True. If True, add info by calling "Print All." after each command.
    :return: rawdata = [
            [ vfile, 
              {
               "command": command,
               "sid": sid,
               "thm": thm,
               "num_goals": num_goals,
               "gid": gid,
               "proof_ctx": ctx,
               "proof_goal": goal,
               "response": response,
               "info": info_msg_list,
               "warning": warning_msg_list,
               "error": error_msg_list,
               }
            ]
            [ vfile,
              {
               ...
              }
            ]
            ...   
        ]

     To process a projlist returned from projpaths_to_projlist function
     argument order should be (proj[2], proj[0], proj[1]) for proj in projlist
     """

    original_wd = os.getcwd()
    os.chdir(proj_dir)
    executable = r"coqtop -emacs" + coq_options
    rawdata = []

    for vfile in tqdm(vfile_list):
        coq = PICoq(executable=executable)
        print(f"\nProcessing {vfile}")

        with open(vfile, "r", encoding="utf-8") as f:
            command_list = separate_commands(f.read())
            for cmd in tqdm(command_list):
<<<<<<< HEAD
                try:
                    retdict_list = coq.enter(cmd)
                    rawdata.append([vfile, retdict_list[0]])
                except:
                    print(f"Error: command: {cmd} failed in file: {vfile}")
=======
                retdict = coq.enter(cmd)[0]
                if printall:
                    printall_dict = coq.enter("Print All.")[0]
                    retdict["response"] = printall_dict["response"] + " " + retdict["response"]
                rawdata.append([vfile, retdict])
>>>>>>> refs/remotes/origin/master

    os.chdir(original_wd)
    return rawdata

def _vfile_checker(vfile, executable="coqtop -emacs", printall=False):
    """
    For Debugging:
    this function tries to execute single vfile
    """
    check_responses = []
    coqoption = ""
    executable = executable + coqoption
    coq = PICoq(executable = executable)
    with open(vfile, "r", encoding="utf-8") as f:
            command_list = separate_commands(f.read())
            for cmd in tqdm(command_list):
                retdict= coq.enter(cmd)[0]
                if printall:
                    printall_dict = coq.enter("Print All.")[0]
                    retdict["response"] = printall_dict["response"] + " " + retdict["response"]
                check_responses.append([f"command : {cmd}",  retdict])
    return check_responses



def rawdata_to_command_moved_up_csv(rawdata, path_csv_file=PATH_TO_DATA_CSV):
    """
    easy to modify this basic function
    to get various train data extraction functions  

    """
    # row = [ 0:sid, 1:thm, 2:num_goals, 3:gid, 4:proof_ctx, 5:proof_goal, 
    #         6:response, 7:info, 8:warning, 9:error, 10:(next)command ]
    with open(path_csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        row = [-1, "", -1, -1, "", "", "", "", "", "", ""]  
        for _ , rd in rawdata:
            row[10] = rd['command']
            writer.writerow(row)
            row = [rd['sid'], rd['thm'], rd['num_goals'], rd['gid'],
                   rd['proof_ctx'], rd['proof_goal'], rd,['response'],
                   "", "","",""] # info, warning, error not implemented
        writer.writerow(row)

        

def rawdata_to_response_commands_T5df(rawdata, prefix="prove in coq", path_csv_file=None):
    """
    source_text : response for each new (sub)goal
    target_text : command1. command2. ... until new (sub)goal appears or proof succeeds

    :param path_csv_file: path to csv file of dataframe data WITHOUT prefix.
    :param prefix: str to use in prefix learning for T5
    :return: dataframe with two columns "source_text", and "target_text"
    """
    # df = pd.read_csv(path_csv_file).astype(str)
    source_target_list = []
    target_text = ""
    source_text = ""
    for _ , rd in rawdata:
        target_text = target_text + " " + rd["command"] # commands accumulate until they (partly) succeed
        if int(rd["num_goals"]) >= 1: # Previous command partly succeeded and the next proof_ctx_goal set.
            source_target_list.append([source_text, target_text])
            source_text = prefix + ": " + rd["response"]
            target_text = ""
        elif int(rd["num_goals"]) == 0: # proof complete
            source_target_list.append([source_text, target_text])
            source_text = ""
        
    df = pd.DataFrame(source_target_list, columns=["source_text", "output_text"])
    if path_csv_file:
        df.to_csv(path_csv_file)
    return df
        
def main(coqproject_pathfile, output_datafile, printall=False):
    """
    :param coqproject_pathfile:
    :param output_datafile:
    :param printall: Defaults to Faulse. 
    If Set True, responses from the coq command "Print All." will be added to data.

    """

    path_obj = pathlib.Path(output_datafile)
    output_datafile = path_obj.resolve() # set absolute path if it was relative

    projlist = projpaths_to_projlist(coqproject_pathfile)
    
    for project in tqdm(projlist):
        print(f"In Project : {project}")
        rawdata = vfiles_to_rawdata(project[2], project[0], project[1], printall)
        df = rawdata_to_response_commands_T5df(rawdata)
        df.to_csv(output_datafile, mode='a', header=False, index=False)
        

    # csv_to_T5df(output_datafile)


if __name__ == "__main__":
    args = sys.argv
    assert len(args) >= 2
    coqproject_pathfile = args[1]
    if len(args) == 2:
        output_datafile = "data.csv"
    else:
        output_datafile = args[2]
    if len(args) >= 4:
        printall = args[3]
        
    main(coqproject_pathfile, output_datafile, printall)
    
