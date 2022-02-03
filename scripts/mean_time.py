import logging

import scripts.test
import xarray


class MeanTimeTest(scripts.test.Test):
    def get_default_args(self):
        return {
            'variable': 'tp',
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
            dataset = opener(location, chunks={'time': int(self.args['time_chunk'])})
        else:
            dataset = opener(location)
        args = self.args
        context.start()
        var = dataset[args['variable']]
        if args['time_range'] != None:
            selection = var.isel(longitude=30, latitude=50, time=range(0, int(args['time_range']) * 365))
        else:
            selection = var.isel(longitude=30, latitude=50)
        mean = selection.mean()
        if self.args['dask'] == '1' or is_zarr:
            mean = mean.compute()
        logging.debug("(%s) Mean at lat/lon index (%d, %d): %.2f", location, 30, 50, mean)
        context.end()
