"""Shared KataGo analysis-engine plumbing for the phase3/phase4 preprocessing scripts."""
import subprocess, json, os, threading, queue

KATAGO_TRT = r"C:\Users\User\source\weiqi_estimator\katago-v1.16.5-trt10.2.0-cuda12.5-windows-x64+bs50\katago.exe"
KATAGO_KATRAIN = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\katago.exe"
MODEL = r"C:\Users\User\Documents\KaTrain\_internal\katrain\models\kata1-b18c384nbt-s9996604416-d4316597426.bin.gz"
CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analysis_bulk.cfg")
STDERR_LOG = "katago_stderr.log"


def default_katago():
    return KATAGO_TRT if os.path.exists(KATAGO_TRT) else KATAGO_KATRAIN


def add_engine_args(parser):
    parser.add_argument('--katago', default=default_katago(), help='Path to katago executable')
    parser.add_argument('--model', default=MODEL, help='Path to model file')
    parser.add_argument('--config', default=CONFIG, help='Path to analysis config')


class Engine:
    """KataGo analysis engine with a reader thread feeding a line queue.

    A None on the queue means the process died (EOF on stdout).
    """

    def __init__(self, katago, model, config):
        self.cmd = [katago, 'analysis', '-config', config, '-model', model]
        self.lines = queue.Queue()
        self._start()

    def _start(self):
        self.stderr = open(STDERR_LOG, 'ab')
        self.proc = subprocess.Popen(
            self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
        )
        threading.Thread(target=self._read, args=(self.proc, self.lines), daemon=True).start()

    @staticmethod
    def _read(proc, q):
        for line in iter(proc.stdout.readline, b''):
            q.put(line)
        q.put(None)

    def send(self, query):
        self.proc.stdin.write((json.dumps(query) + '\n').encode())
        self.proc.stdin.flush()

    def restart(self):
        self.stop()
        self._start()

    def stop(self):
        try:
            self.proc.terminate()
        except Exception:
            pass
        try:
            self.stderr.close()
        except Exception:
            pass
