# picoq.py : Python Interface for Coq
# by Ken'ichi Kuga ....
# (C) 2017 Chiba University???
# License GNU GPL???

# Set your proof assistant excutable:
PA_EXCUTABLE = r"coqtop -emacs"
# PA_EXCUTABLE = r'coqtop -toploop coqidetop -main-channel stdfds'

# Set exaustive re-pattern of ending strings
# of responses from your proof assisant.
# Those are typically r'propmt_string$'.

PA_PROMPT = r"(<prompt>.*</prompt>$)"  # |(Syntax error: [^.]+\.)|(Error: [^.]+\.)'
PA_THEOREM_NAME = r"<prompt>(.*) < (\d+) \|(.*)\| (\d+) < </prompt>$"
PA_INFO = r"^<infomsg>(.*)</infomsg>$"
PA_DEFINED = r"(.*) is defined"
PA_NO_MORE_GOALS = r"^No more (sub)?goals.$"
PA_ERROR = r"\r\nError:"
PA_WARNING = r"^<warning>(.*)</warning>$"
PA_PROOF_DGM = r"==================+\r\n"

# PROOF_STATUS = ['GOAL_UPDATED', 'PROVING', 'NO_MORE_GOALS' ,'DEFINED', 'ERROR','NOT_IN_PROOF']

# Set your max time to wait responses (in seconds):
TIMEOUT = 10  # 60

from pipas import PIProofAssistant
import re

# Example of model preparation
# To use simplet5 we need to install sentencepiece first
# trained data is also required
from simplet5 import SimpleT5

model = SimpleT5()
model.from_pretrained("t5", "t5-base")
model.load_model(
    "t5", "outputs/simplet5-epoch-4-train-loss-0.8944-val-loss-0.8247", use_gpu=False
)
#
#


class PICoq(PIProofAssistant):
    re_info = re.compile(PA_INFO)
    re_defined = re.compile(PA_DEFINED)
    re_theorem_name = re.compile(PA_THEOREM_NAME)
    re_error = re.compile(PA_ERROR)
    re_proof_dgm = re.compile(PA_PROOF_DGM)
    re_no_more_goals = re.compile(PA_NO_MORE_GOALS)

    def __init__(
        self,
        pa_executable=PA_EXCUTABLE,
        prompt=PA_PROMPT,
        args=[],
        timeout=TIMEOUT,
        maxread=2000,
        searchwindowsize=None,
        logfile=None,
        cwd=None,
        env=None,
        ignore_sighup=False,
        echo=False,
        preexec_fn=None,
        encoding=None,
        codec_errors="strict",
        dimensions=None,
        with_model=None,
    ):
        super(PICoq, self).__init__(
            pa_executable,
            prompt,
            args,
            timeout,
            maxread,
            searchwindowsize,
            logfile,
            cwd,
            env,
            ignore_sighup,
            echo,
            preexec_fn,
            encoding,
            codec_errors,
            dimensions,
        )

        self._response = ""
        self._resp_after = ""
        self._theorem_name = "Coq"
        self._error = ""
        self._proof_dgm = ""
        self._no_more_goals = None
        self._proof_status = "NOT_IN_PROOF"

        if with_model != None:
            self.model = with_model

    def enter(self, command):

        command = command.rstrip()
        if len(command) != 0 and command[-1] != ".":
            print("Error: command must end with a period '.'")
            return

        response, resp_after = super(PICoq, self).enter(command)

        self._command = command
        self._response = response
        self._resp_after = resp_after
        self._proof_dgm = ""

        m = self.re_theorem_name.search(self._resp_after)
        previous_theorem_name = self._theorem_name
        self._theorem_name = m.group(1)

        if self._theorem_name == "Coq":

            if previous_theorem_name == "Coq":
                self._proof_status = "NOT_IN_PROOF"

            else:
                self._proof_status = "DEFINED"

        elif self.re_proof_dgm.search(self._response):
            self._proof_dgm = self._response
            self._proof_status = "GOAL_UPDATED"

        else:
            self._proof_dgm = ""

            if self.re_no_more_goals.match(self._response):
                self._proof_status = "NO_MORE_GOALS"

            elif self.re_error.search(self._response):
                self._proof_status = "ERROR"

            else:
                self._proof_status = "PROVING"

        retdict = {
            "theorem_name": self._theorem_name,
            "proof_dgm": self._proof_dgm,
            "command": self._command,
            "proof_status": self._proof_status,
            "response": self._response,
        }

        print(retdict["response"] + "\n" + retdict["proof_status"])  # For Debugging

        return retdict

    def close(self):
        self.enter("Quit.")
        super(PICoq, self).close()  ### ???

    # Clean the raw string returned from stdout/stderr.read()
    def _format(self, string):
        string = string.decode("cp1252")
        string = string.strip()
        return "".join([c for c in string if ord(c) < 128])

    def get_info(self):
        m = self.re_info.search(self._response)
        self._info = m.group(0)
        return self._info


"""
    def is_no_goal_left(self):
        self._no_more_goals = self.re_no_more_goals.match(self._response)
        return self._no_more_goals

    def is_proof_dgm(self):
        return self.re_proof_dgm.search(self._response)

    def is_error(self):
        self._error = self.re_error.search(self._response)
        return self._error
"""
