import logging

import scripts.test
import xarray


class MeanAreaTest(scripts.test.Test):
    def get_default_args(self):
        return {
            'variable': 'tp',
            'time_var': 'time',
            'time': '10',
            'dask': '0'
        }

    def do_test(self, context):
        location = context.input
        dataset = self.open_dataset(context)
        args = self.args
        time = int(args['time'])
        selector = {args['time_var']: time}
        context.start()
        var = dataset[args['variable']]
        selection = var.isel(selector)
        mean = selection.mean()
        logging.debug("(%s) Mean at time index %d: %.2f", location, time, mean)
        if self.is_zarr_archive(context) or self.is_dask_enabled():
            mean = mean.compute()
        
        context.end()
