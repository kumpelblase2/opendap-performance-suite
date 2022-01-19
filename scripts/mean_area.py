import logging

import scripts.test
import xarray


class MeanAreaTest(scripts.test.Test):
    def __init__(self, variable='tp', time=10):
        self.variable = variable
        self.time_slot = time
        super().__init__()

    def do_test(self, context):
        location = context.file
        context.start()
        dataset = xarray.open_dataset(location)
        var = dataset[self.variable]
        selection = var.isel(time=self.time_slot)
        mean = selection.mean()
        logging.debug("(%s) Mean at time index %d: %.2f", location, self.time_slot, mean)
        context.end()
