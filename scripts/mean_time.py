import logging

import scripts.test
import xarray


class MeanTimeTest(scripts.test.Test):
    def get_default_args(self):
        return {
            'variable': 'tp',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'time': 'time',
            'time_range': None,
            'dask': '0',
            'time_chunk': '100'
        }

    def do_test(self, context):
        location = context.file
        opener = xarray.open_dataset
        is_zarr = False
        if location[-5:] == '.zarr':
            opener = xarray.open_zarr
            is_zarr = True

        if self.args['dask'] == '1':
            dataset = opener(location, chunks={self.args['time']: int(self.args['time_chunk'])})
        else:
            dataset = opener(location)
        args = self.args
        var = dataset[args['variable']]
        selection_def = {
            args['longitude']: 30,
            args['latitude']: 30
        }
        if args['time_range'] != None:
            selection_def[args['time']] = range(0, int(args['time_range']) * 365)
        context.start()
        selection = var.isel(selection_def)
        mean = selection.mean()
        if self.args['dask'] == '1' or is_zarr:
            mean = mean.compute()
        logging.debug("(%s) Mean at lat/lon index (%d, %d): %.2f", location, 30, 50, mean)
        context.end()
