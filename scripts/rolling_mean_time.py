import logging

import scripts.test
import xarray
import numpy

def mean_fnc(group, ds):
    ds.isel({'time': group}).mean()

class RollingMeanTimeTest(scripts.test.Test):
    def get_default_args(self):
        return {
            'variable': 'tp',
            'time_var': 'time',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'dask': '0',
            'separate': '0'
        }

    def group_time(self, time_dim, variable_dim):
        if time_dim.dtype.name.startswith('datetime'):
            return time_dim.groupby('time.month')
        else:
            return numpy.array_split(time_dim, 365)

    def do_test(self, context):
        location = context.input
        args = self.args
        if self.is_dask_enabled():
            dataset = self.open_dataset(context, chunks={args['time_var']:1, args['longitude']:1440, args['latitude']: 721})
        else:
            dataset = self.open_dataset(context)

        if self.is_unstructured(dataset):
            selection_def = { 'ncells' : 120 }
        else:
            selection_def = {
                args['longitude']: 30,
                args['latitude']: 30
            }
        
        context.start()
        selection = dataset[args['variable']].isel(selection_def)
        if args['separate'] == '1':
            groups = self.group_time(dataset[args['time_var']], selection)
            mean_values = []
            for (index, values) in groups:
                selection_group = selection.sel({args['time_var']: values})
                mean_values.append(selection_group.mean())
            
            if self.is_dask_enabled():
                import dask.array
                mean_values = dask.array.from_array(mean_values).compute()
        else:
            groups = selection.groupby('time.month')
            mean_values = groups.mean()
            if self.is_lazy(mean_values) or self.is_zarr_archive(context):
                mean_values = mean_values.compute()    

        context.end()
        logging.debug(f"Mean values: {mean_values}")
