# pipas.py :  Abstract Class for Python Interface for Proof Assistant Systems
# by Ken'ichi Kuga ....
# (C) 2017 Chiba University???
# License GNU GPL???

import signal
import pexpect
import re

# Base class for proof assistant processes.
# prompt parameter is a re-pattern matching the end of responses: typicall  r'prompt_string$'
# Other parameters are handded to pexpect.spawn class.
class PIProofAssistant(object):
    # initializer
    def __init__(
        self,
        pa_executable,
        prompt,
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
        encoding=None,
        codec_errors="strict",
        dimensions=None,
    ):
        self._pa_executable = pa_executable
        self._prompt = prompt
        self._args = args
        self._timeout = timeout
        self._maxread = maxread
        self._searchwindowsize = searchwindowsize
        self._logfile = logfile
        self._cwd = cwd
        self._ignore_sighup = ignore_sighup
        self._echo = echo
        self._preexec_fn = preexec_fn
        self._encoding = encoding
        self._codec_errors = codec_errors
        self._dimensions = dimensions
        self._response = ""
        self._resp_after = ""
        self._theorem_name = ""
        self._info = ""
        self._warning = ""
        self._error = ""
        self._pa_process = None
        self._pa_process = pexpect.spawn(
            pa_executable,
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
        self._pa_process.setecho(False)
        self.enter("")

    def __del__(self):
        if self._pa_process:
            self._pa_process.close()

    def close(self):
        self.__del__()

    def interrupt(self):
        self._pa_process.kill(signal.SIGINT)

    def enter(self, command):
        self._pa_process.sendline(command)
        response = ""
        resp_after = ""
        index = self._pa_process.expect([self._prompt, pexpect.EOF])
        if index == 1:
            response = "Process stopped."
        else:
            response = self._format(self._pa_process.before)
            resp_after = self._format(self._pa_process.after)
            self._response = response
            self._resp_after = resp_after
        return response, resp_after

    def get_response(self):
        return self._response

    def get_info(self):
        pass

    def get_warning(self):
        pass

    def get_error(self):
        return self.error

    def is_defined(self):
        pass

    # _real() sets _error with the string returned after prompt
    # returnes the string before prompt.
    def _read(self):
        self._pa_process.expect(self._prompt)
        self._error = self._pa_process.after
        return self._format(self._pa_process.before)

    # Override this method to format raw _pa_process.before
    def _format(self, data):
        pass

    # TODO : implement basic commands and tactics
    # so that python code can handle them directly and uniformly among different proof assistants.

    # abstract rewrite
    def rewrite(self, args):
        pass

    # abstract
    def get_state_label(self):
        pass

    # abstract
    def GoBackTo(self, state_label):
        pass

    # abstract
    def GetScriptFile(self):
        pass
