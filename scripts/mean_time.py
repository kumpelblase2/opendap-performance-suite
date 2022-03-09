import logging

import scripts.test

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
        if self.is_dask_enabled():
            dataset = self.open_dataset(context, chunks={self.args['time']: int(self.args['time_chunk'])})
        else:
            dataset = self.open_dataset(context)

        args = self.args
        var = dataset[args['variable']]
        if self.is_unstructured(dataset):
            selection_def = { 'ncells' : 120 }
        else:
            selection_def = {
                args['longitude']: 30,
                args['latitude']: 30
            }

        
        if args['time_range'] != None:
            selection_def[args['time']] = range(0, int(args['time_range']) * 365)

        context.start()
        selection = var.isel(selection_def)
        mean = selection.mean()
        if self.is_dask_enabled() or self.is_zarr_archive(context):
            mean = mean.compute()
        logging.debug("(%s) Mean at lat/lon index (%d, %d): %.2f", context.input, 30, 50, mean)
        context.end()
