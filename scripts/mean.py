import logging

import scripts.test
import xarray


class MeanTest(scripts.test.Test):
    def __init__(self, variable='tp', time=10):
        self.variable = variable
        self.time_slot = time
        super().__init__()

    def do_test(self, context):
        location = context.file
        context.start()
        dataset = xarray.open_dataset(location)
        var = dataset[self.variable]
        selection = var.isel(longitude=slice(0, 15), latitude=slice(23, 65), time=self.time_slot)
        mean = selection.mean()
        logging.debug("(%s) Mean: %.2f", location, mean)
        context.end()
