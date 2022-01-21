import logging

import scripts.test
import xarray


class MeanTimeTest(scripts.test.Test):
    def get_default_args(self):
        return {
            'variable': 'tp',
            'time_range': None
        }

    def do_test(self, context):
        location = context.file
        dataset = xarray.open_dataset(location)
        args = self.args
        context.start()
        var = dataset[args['variable']]
        if args['time_range'] != None:
            selection = var.isel(longitude=30, latitude=50, time=range(0, int(args['time_range']) * 365))
        else:
            selection = var.isel(longitude=30, latitude=50)
        mean = selection.mean()
        logging.debug("(%s) Mean at lat/lon index (%d, %d): %.2f", location, 30, 50, mean)
        context.end()
