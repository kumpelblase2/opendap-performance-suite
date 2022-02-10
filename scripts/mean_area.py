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
        location = context.file
        args = self.args
        time = int(args['time'])
        if args['dask'] == '1':
            logging.info('Dask is enabled, but it will not be used on mean-area.')
        dataset = xarray.open_dataset(location)
        selector = {args['time_var']: time}
        context.start()
        var = dataset[args['variable']]
        selection = var.isel(selector)
        mean = selection.mean()
        logging.debug("(%s) Mean at time index %d: %.2f", location, time, mean)
        context.end()
