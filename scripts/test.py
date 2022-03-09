from dask.distributed import Client
from abc import abstractmethod
import time
import xarray


class Context:
    def __init__(self):
        self.file_data = {}
        self.runs = []
        self.times = {}
        self.start_times = {}
        self.input = None

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
        self.input = file

    def finish_file(self):
        if isinstance(self.input, list):
            self.file_data['|'.join(self.input)] = self.runs
        else:
            self.file_data[self.input] = self.runs
        self.runs = []
        self.input = None


class Test:
    def __init__(self):
        self.default_args = self.get_default_args()

    @abstractmethod
    def get_default_args(self):
        pass

    @abstractmethod
    def do_test(self, context):
        pass

    def is_dask_enabled(self):
        return self.args['dask'] == '1'

    def is_zarr_archive(self, context):
        if isinstance(context.input, str):
            return context.input[-5:] == '.zarr'
        else:
            return False
    
    def is_multi_dataset(self, context):
        return isinstance(context.input, list)

    def open_dataset(self, context, **kwargs):
        if self.is_zarr_archive(context):
            return xarray.open_zarr(context.input, **kwargs)
        elif self.is_multi_dataset(context):
            return xarray.open_mfdataset(context.input, **kwargs)
        else:
            return xarray.open_dataset(context.input, **kwargs)
    
    def is_unstructured(self, ds):
        return 'ncells' in ds.dims

    def run(self, files, reruns, args):
        context = Context()
        self.args = self.default_args | args
        for file in files:
            context.update_file(file)
            if self.is_dask_enabled():
                c = Client('localhost:8786')

            for i in range(reruns):
                self.do_test(context)
                context.finish_run()
            
            if self.is_dask_enabled():
                c.close()

            context.finish_file()
        return context.file_data
