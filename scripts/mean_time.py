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
            'time_chunk': '100',
            'height_var': None,
            'height': '0',
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
            lat_var = [key for key in ['lat', 'latitude', args['latitude']] if key in dataset.dims.keys()][0]
            lon_var = [key for key in ['lon', 'longitude', args['longitude']] if key in dataset.dims.keys()][0]

            selection_def = {
                lon_var: 30,
                lat_var: 30
            }

        
        if args['time_range'] != None:
            selection_def[args['time']] = range(0, int(args['time_range']) * 365)

        if args['height_var'] is not None:
            selection_def[args['height_var']] = int(args['height'])

        context.start()
        selection = var.isel(selection_def)
        mean = selection.mean()
        if self.is_dask_enabled() or self.is_zarr_archive(context) or self.is_lazy(mean):
            mean = mean.compute()
        logging.debug("(%s) Mean at lat/lon index (%d, %d): %.2f", context.input, 30, 30, mean)
        context.end()
