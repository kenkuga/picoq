import sys
import os
import re
import glob
import csv
from typing_extensions import dataclass_transform
from picoq import PICoq
import pandas as pd

R_option_pat = re.compile(r"^\s*-R (.+?) (.+?)$")
v_file_pat = re.compile(r"^/s*.+?\.v$")


def read_coqprojects(coqproj_pathfile: str) -> list:
    projlist = []
    with open(coqproj_pathfile, "r") as cppf:
        proj_paths = cppf.readlines()
        for path in proj_paths:
            path = path.strip()
            if path[-1] == "/":
                path = path[:-1]
            os.chdir(path)
            proj = [path]
            r_ops = ""
            v_files = []
            if os.path.isfile("_CoqProject"):
                with open("./_CoqProject") as cp:
                    cp_list = cp.readlines()
                    for line in cp_list:
                        line = line.strip()
                        rmatch = R_option_pat.match(line)
                        vmatch = v_file_pat.match(line)
                        if rmatch:
                            r_ops = r_ops + " " + rmatch.group(0)
            if len(v_files) == 0:
                v_files = glob.glob(path + "/**/*.v", recursive=True)
                print(f"No R-options in {path}")
            proj.append(r_ops)
            proj.append(v_files)
            projlist.append(proj)
    return projlist  # [ ["path_to_project", "-R options", ["file1.v", "file2.v, ..."]], ...]


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
    return [code + "." for code in codes if code != ""]


def coq_to_data(coq_options, vfile_list, out_csv_file):
    print(f"coq_to_data callded with {coq_options}, {vfile_list}")  # FOR DEBUGGING
    pa_executable = r"coqtop -emacs" + coq_options
    writer = csv.writer(out_csv_file, quoting=csv.QUOTE_ALL)

    for vfile in vfile_list:

        coq = PICoq(pa_executable=pa_executable)
        print(f"coq processing {vfile}")

        with open(vfile, "r", encoding="utf-8") as f:
            data = []
            codes = clean_codes(f.read())
            proof_dgm = ""
            tactics = ""
            for code in codes:
                rdict = coq.enter(code)
                if rdict["proof_status"] == "NOT_IN_PROOF":
                    continue
                elif rdict["proof_status"] == "GOAL_UPDATED":
                    if proof_dgm != "":
                        data.append([proof_dgm, tactics + " " + code])
                    proof_dgm = rdict["proof_dgm"]
                    tactics = ""
                elif rdict["proof_status"] == "PROVING":
                    tactics = tactics + " " + code
                elif rdict["proof_status"] == "NO_MORE_GOALS":
                    data.append([proof_dgm, tactics + " " + code])
                    proof_dgm = ""
                    tactics = ""
                else:
                    continue
                # print(f"****************************************DEBUGGING data = {data} ") ## DEBUGGING
            writer.writerows(data)
            out_csv_file.flush()
            os.fsync(out_csv_file.fileno())
            print("\n###################################################\n")
            num_data = len(data)
            print(f"data contains {num_data} pairs.\n")
            # print(data)
            print("###################################################\n\n")

        coq.close()


"""class Coq2T5(object):
    def __init__(self, pa_executable="coqtop -emacs"):
        self.pa_executable = pa_executable"""


def csv_to_T5df(path_csv_file):
    df = pd.read_csv(path_csv_file).astype(str)
    df.columns = ["input_text", "target_text"]
    df["prefix"] = "Prove in Coq"
    return df


if __name__ == "__main__":
    args = sys.argv
    assert len(args) == 2 or len(args) == 3
    coqproject_pathfile = args[1]
    if len(args) == 2:
        output_datafile = "/Users/kenkuga/Desktop/coq_theorem_proof_data.csv"
    else:
        output_datafile = args[2]
    projlist = read_coqprojects(coqproject_pathfile)
    with open(output_datafile, mode="a") as csv_file:
        for project in projlist:
            print(f"In Project : {project}")
            R_option = project[1]
            coq_to_data(R_option, project[2], csv_file)

    # csv_to_T5df(output_datafile)
