# picoq.py : Python Interface for Coq
# Author Kenichi Kuga
# License

import pexpect
import re
from utils import separate_commands

EXCUTABLE = r"coqtop -emacs"
TIMEOUT = 10
MAXREAD = 2000

PROMPT_PAT = r"<prompt>(.*) < (?P<sid>\d+) \|(?P<thm>.*)\| (\d+) < </prompt>"
PROOF_DGM_PAT = r"^(?P<num_g>\d+) goals? \(ID (?P<gid>\d+)\)\r\n\s*(?P<context>.*)\r\n\s*==================+\r\n\s*(?P<goal>.+)"
# DEFINED_PAT = r"(.*) is defined"
NO_MORE_GOALS_PAT = r"^No more (sub)?goals\."
INFO_MSG_PAT = r"<infomsg>(.*?)</infomsg>"
WARNING_MSG_PAT = r"<warning>\r\nWarning: (.*?)</warning>"
ERROR_MSG_PAT = r".*Error: (?P<error_type>.+ error: )?(?P<error_msg>[^.]+)\."

PRINT_ALL_PAT = r'( >>>>>>> \w+ \w+\r\n)*?\*\*\* (\[\w+ : [^\]]+\]\r\n\r\n)*?\r\n\r\n' # NOT TESTED

# re_prompt = re.compile(PROMPT_PAT)
re_proof_dgm = re.compile(PROOF_DGM_PAT, re.DOTALL)
# re_defined = re.compile(DEFINED_PAT)
re_no_more_goals = re.compile(NO_MORE_GOALS_PAT)
re_info_msg = re.compile(INFO_MSG_PAT, re.DOTALL)
re_warning_msg = re.compile(WARNING_MSG_PAT, re.DOTALL)
re_error_msg = re.compile(ERROR_MSG_PAT, re.DOTALL)
re_print_all_msg = re.compile(PRINT_ALL_PAT)  # NOT TESTED

class PICoq(object):
    def __init__(
        self,
        executable=EXCUTABLE,
        prompt=PROMPT_PAT,
        args=[],
        timeout=30,
        maxread=2000,
        searchwindowsize=None,
        logfile=None,
        cwd=None,
        env=None,
        ignore_sighup=False,
        echo=False,
        preexec_fn=None,
        encoding="utf-8",  # None
        codec_errors="strict",
        dimensions=None,
    ):
        self.executable = executable
        self.prompt = prompt
        self.timedout = timeout
        self.maxread = maxread
        self.echo = echo
        self.encoding = encoding
        self.codec_errors = codec_errors

        self.process = None
        self.process = pexpect.spawn(
            executable,
            args=args,
            timeout=timeout,
            maxread=maxread,
            searchwindowsize=searchwindowsize,
            logfile=logfile,
            cwd=cwd,
            env=env,
            ignore_sighup=ignore_sighup,
            echo=echo,
            preexec_fn=preexec_fn,
            encoding=encoding,
            codec_errors=codec_errors,
            dimensions=dimensions,
        )
        self.process.setecho(False)
        self.process.expect(self.prompt)

        self.enter("Set Printing Parentheses.")  # Optional Setting(s)

    def enter(self, commands):
        command_list = separate_commands(commands)
        responses = []

        for cmd in command_list:
            
            prompt_group = self.process.match.group
            sid = prompt_group("sid")
            thm = prompt_group("thm")
            
            self.process.sendline(cmd)
            self.process.expect(self.prompt)
            response = self.process.before # response = self.decord_to_str(self.process.before)
        
            num_goals = -1 
            gid = -1
            ctx = ""
            goal = ""
            info_msg_list = []
            warning_msg_list = []
            error_msg_list = []

            proof_match = re_proof_dgm.match(response)
            if proof_match:
                proof_group = proof_match.group
                num_goals = proof_group("num_g")
                gid = proof_group("gid")
                ctx = proof_group("context")
                goal = proof_group("goal")
            elif re_no_more_goals.match(response):
                num_goals = 0 # proof success

            info_msg_list = re_info_msg.findall(response)
            warning_msg_list = re_warning_msg.findall(response)
            if num_goals== -1:
                error_m = re_error_msg.match(response)  # NEED TO DO
                if error_m:
                    error_msg_list.append(error_m.group(0)) # NEED TO DO

            respdict = {
                "command": cmd,
                "sid": sid,
                "thm": thm,
                "num_goals": num_goals,
                "gid": gid,
                "proof_ctx": re.sub(r'\r\n', '',ctx),
                "proof_goal": re.sub(r'\r\n', '',goal),
                "response": re.sub(r'\r\n', '',response),
                "info": info_msg_list,
                "warning": warning_msg_list,
                "error": error_msg_list,
            }
            responses.append(respdict)
        return responses


    def close(self):
        if self.process:
            # self.enter("Quit.")
            self.process.close() 

    def __call__(self, commands):
        return self.enter(commands)

    # Clean the raw string returned from stdout/stderr.read()
    # Not used now.
    def decord_to_str(self, bytes_like):
        string = bytes_like.decode("cp1252")
        string = string.strip()
        return "".join([c for c in string if ord(c) < 128])
