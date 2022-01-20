import logging

import scripts.test
import xarray


class MeanTimeTest(scripts.test.Test):
    def __init__(self, variable='tp', time_range=None):
        self.variable = variable
        self.time_range = time_range
        super().__init__()

    def do_test(self, context):
        location = context.file
        context.start()
        dataset = xarray.open_dataset(location)
        var = dataset[self.variable]
        if self.time_range != None:
            selection = var.isel(longitude=30, latitude=50, time=self.time_range)
        else:
            selection = var.isel(longitude=30, latitude=50)
        mean = selection.mean()
        logging.debug("(%s) Mean at lat/lon index (%d, %d): %.2f", location, 30, 50, mean)
        context.end()
