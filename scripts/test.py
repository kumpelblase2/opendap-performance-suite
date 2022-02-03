from dask.distributed import Client
from abc import abstractmethod
import time


class Context:
    def __init__(self):
        self.file_data = {}
        self.runs = []
        self.times = {}
        self.start_times = {}
        self.file = None

    def start(self, name='default'):
        self.start_times[name] = time.time()

    def end(self, name='default'):
        current = time.time()
        start = self.start_times[name]
        self.times[name] = {
            'start': start,
            'end': current,
            'total': current - start
        }
        self.start_times.pop(name)

    def finish_run(self):
        self.runs.append(self.times)
        self.times = {}

    def update_file(self, file):
        self.file = file

    def finish_file(self):
        self.file_data[self.file] = self.runs
        self.runs = []
        self.file = None


class Test:
    def __init__(self):
        self.default_args = self.get_default_args()

    @abstractmethod
    def get_default_args(self):
        pass

    @abstractmethod
    def do_test(self, context):
        pass

    def run(self, files, reruns, args):
        context = Context()
        self.args = self.default_args | args
        for file in files:
            context.update_file(file)
            if self.args['dask'] == '1':
                c = Client('localhost:8786')

            for i in range(reruns):
                self.do_test(context)
                context.finish_run()
            
            if self.args['dask'] == '1':
                c.close()

            context.finish_file()
        return context.file_data
