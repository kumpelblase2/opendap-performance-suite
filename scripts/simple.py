import logging

import scripts.test
import xarray


class SimpleTest(scripts.test.Test):
    def do_test(self, context):
        location = context.file
        context.start()
        dataset = xarray.open_dataset(location)
        attributes = dataset.attrs
        # we just want to make sure that at least the metadata gets loaded
        # we don't really care about anything else in this test
        _attr_count = len(attributes)
        coords = dataset.coords
        logging.debug('(%s) Coords: %s, Attribute Count: %d', location, ','.join(coords.keys()), len(attributes.keys()))
        context.end()
