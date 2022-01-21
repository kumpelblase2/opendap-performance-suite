import logging

import scripts.test
import xarray


class MeanAreaTest(scripts.test.Test):
    def get_default_args(self):
        return {
            'variable': 'tp',
            'time': '10'
        }

    def do_test(self, context):
        location = context.file
        args = self.args
        dataset = xarray.open_dataset(location)
        context.start()
        var = dataset[args['variable']]
        selection = var.isel(time=int(args.time))
        mean = selection.mean()
        logging.debug("(%s) Mean at time index %d: %.2f", location, int(args.time), mean)
        context.end()
