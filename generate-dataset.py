import xarray
import numpy
import argparse
import re
import datetime

SPLIT_OPTIONS=['time', 'area']
DISTRIBUTION_REGEX = re.compile('(\w+)(\(([0-9\.\-]+(, ?[0-9\.\-])*)\))?')

parser = argparse.ArgumentParser(description='Generate synthetic datasets for testing with 2 (unstructured) or 3 (grid) dimensions with one or more variables.')

parser.add_argument('file', metavar='OUTPUT', type=str, help='The name of the file to write the output to. When multiple files will generated, the files will be called "<name>_0", "<name>_1", etc.')
parser.add_argument('--time-values', '-t', type=int, default=365, help='How many time entries')
parser.add_argument('--vars', '-V', type=int, default=1, help='Amount of variables to create')
parser.add_argument('--grid', '-g', type=float, help='Use a normal grid with the given resolution')
parser.add_argument('--unstructured', '-u', type=int, help='Use an unstructured grid with the given amount of cells')
parser.add_argument('--split', '-s', type=str, choices=SPLIT_OPTIONS, default='time', help='Along where to split files')
parser.add_argument('--split-count', '-f', type=int, default=1, help='Amount of files to split int')
parser.add_argument('--chunking', '-c', type=str, help='Chunking in the format "<var>=<size>,<var>=<size>,..."')
parser.add_argument('--compression', '-C', type=int, help='Compression level for variables')
parser.add_argument('--rng-seed', '-r', type=int, help='Seed for randomizer')
parser.add_argument('--no-shuffle', '-S', default=False, action='store_true', help='Disable shuffling when compressing data')
parser.add_argument('--distribution', '-d', type=str, help='Which distribution model to use for random variables. Format is "<distribution>(<arg1>, <arg2>,...)"')
parser.add_argument('--netcdf3', '-3', default=False, action='store_true', help='Output a NetCDF3 file instead of a NetCDF4')
parser.add_argument('--height', '-H', type=int, default=None, help='Add a fourth dimension - height - with the given amount of entries')
parser.add_argument('--zarr', '-z', default=False, action='store_true', help='Output a zarr store')
parser.add_argument('--verbose', '-v', default=False, action='store_true')
parser.add_argument('--datetime', '-D', default=False, action='store_true', help='Use datetime values instead of int for time dimension')

def generate_file(args, index, rng_func, extra_attributes):
    if args.verbose:
        print(f"Generating file {index}...")
    grid = generate_grid(args, index)
    vars = [generate_var(grid, rng_func) for i in range(0, args.vars)]

    if args.grid is not None:
        coords = {
            'time': ('time', grid[0]),
            'longitude': ('longitude', grid[-2]), # Use negative indexing to handle possible height dim
            'latitude': ('latitude', grid[-1]),
        }
    else:
        coords = {
            'time': ('time', grid[0]),
            'ncells': ('ncells', grid[-1])
        }

    dims = list(coords.keys())
    
    if args.height is not None:
        coords['height'] = ('height', grid[1])
        dims.insert(1, 'height')

    var_dict = {}
    for i, var in enumerate(vars):
        var_dict[f"var_{i}"] = (dims, var)

    chunking = parse_chunking(args.chunking, dims) if args.chunking is not None else None
    encoding = {}
    for i in range(0, len(vars)):
        var_name = f'var_{i}'
        encode_vars = {}
        if args.compression is not None:
            encode_vars = encode_vars | dict(zlib=True, complevel=args.compression, shuffle=(not args.no_shuffle))
        
        if chunking is not None:
            encode_vars = encode_vars | dict(chunksizes=chunking)

        if len(encode_vars.keys()) > 0:
            encoding[var_name] = encode_vars

    if args.datetime:
        # We need to set this because dap2 does not support int64 types
        encoding['time'] = { 'dtype': 'float64' }

    ds = xarray.Dataset(data_vars=var_dict, coords=coords, attrs=extra_attributes)
    kwargs = {}
    if args.netcdf3:
        kwargs['format'] = 'NETCDF3_CLASSIC'

    if len(encoding.keys()) > 0:
        kwargs['encoding'] = encoding
    
    if not args.zarr:
        if args.split == 'time':
            kwargs['unlimited_dims'] = ['time']
        elif args.grid is not None:
            kwargs['unlimited_dims'] = ['longitude', 'latitude']
    
    if args.verbose:
        print(f"Encoding set to {kwargs}")
    
    if args.zarr:
        kwargs = convert_to_zarr_args(args, kwargs)
        ds.to_zarr(**kwargs)
    else:
        ds.to_netcdf(f"{args.file}_{index}.nc", **kwargs)

def generate_grid(args, index):
    if args.grid is not None:
        resolution = args.grid
        if args.split == 'time':
            longitude = numpy.arange(0, 360, resolution)
            latitude = numpy.arange(-90, 90, resolution)
            time = generate_time_dim(args, index)
            if args.height is not None:
                height = numpy.arange(0, args.height)
                return [time, height, longitude, latitude]

            return [time, longitude, latitude]
        elif args.split == 'area':
            time = generate_time_dim(args, index)
            if args.split_count % 2 != 1:
                print("Split count needs to be a multiple of two when using area")
                exit(1)
            
            [longitude, latitude] = generate_area(resolution, args.split_count, index)
            if args.height is not None:
                height = numpy.arange(0, args.height)
                return [time, height, longitude, latitude]

            return [time, longitude, latitude]

    else:
        if args.split == 'time':
            cells = args.unstructured
            time = generate_time_dim(args, index)
            cells = numpy.arange(cells)
            if args.height is not None:
                height = numpy.arange(0, args.height)
                return [time, height, cells]
            return [time, cells]
        elif args.split == 'area':
            cells_per_file = args.unstructured / args.split_count
            time = generate_time_dim(args, index)
            cells = numpy.arange(index * cells_per_file, (index + 1) * cells_per_file)
            if args.height is not None:
                height = numpy.arange(0, args.height)
                return [time, height, cells]
            return [time, cells]

def generate_time_dim(args, index):
    if args.split == 'time':
        if args.datetime:
            return generate_datetime_slice(args.time_values, args.split_count, index)
        else:
            return generate_time_slice(args.time_values, args.split_count, index)
    elif args.split == 'area':
        if args.datetime:
            time = generate_datetime_slice(args.time_values, 1, 0)
        else:
            time = generate_time_slice(args.time_values, 1, 0)

def generate_datetime_slice(values, splits, index, offset=0):
    time_per_file = int(values / splits)
    start = datetime.datetime(2000, 1, 1) + datetime.timedelta(days=offset) + datetime.timedelta(days=index * time_per_file)
    end = start + datetime.timedelta(days = time_per_file)
    return numpy.arange(start, end, datetime.timedelta(days=1))

def generate_time_slice(values, splits, index, offset=0):
    time_per_file = int(values / splits)
    return numpy.arange(index * time_per_file + offset, (index + 1) * time_per_file + offset, dtype=numpy.int32)

def generate_area(resolution, splits, index):
    [subarea_x, subarea_y] = get_area_size(splits)
    size_x = (360.0 / resolution) * subarea_x
    size_y = (180.0 / resolution) * subarea_y
    x_indices = (1 / subarea_x)
    x_index = index % x_indices
    y_index = int(index / x_indices)

    longitude = np.arange(x_index * (360 * subarea_x), (x_index + 1) * (360 * subarea_x), resolution) # x?
    latitude = np.arange(y_index * (180 * subarea_y), (y_index + 1) * (180 * subarea_y), resolution) # y?
    return [longitude, latitude]

def get_area_size(count):
    which = 'x'
    x = 1
    y = 1
    for i in range(0, int(count / 2)):
        if which == 'x':
            x = x / 2
            which = 'y'
        else:
            y = y / 2
            which = 'x'
    return [x, y]

def generate_var(grid, rng_func):
    return rng_func(tuple(map(lambda dim: len(dim), grid)))

def parse_chunking(string, dims):
    var_chunks = string.split(',')
    key_value_arrays = [var.split('=') for var in var_chunks]
    chunking = {key_value[0]: key_value[1] for key_value in key_value_arrays}
    try:
        return tuple(map(lambda dim: int(chunking[dim]), dims))
    except KeyError as e:
        print(f"Dimension is not specified in chunk description: {e}")
        exit(1)

def parse_distribution(dist):
    matched = DISTRIBUTION_REGEX.match(dist)
    if matched:
        name = matched.group(1)
        args = matched.group(3)
        if args:
            args = [float(value) for value in args.split(',')]
        else:
            args = []
        
        return [name, args]        
    else:
        print("Could not evaluate distribution")
        exit(1)

def get_random_func(rng, args):
    if args.distribution is not None:
        [dist, args] = parse_distribution(args.distribution)
        func = getattr(rng, dist)
        return lambda x: func(*args, x)

    return rng.random

def convert_to_zarr_args(args, kwargs):
    import zarr
    new_args = {
        'store': f"{args.file}.zarr"
    }

    if 'encoding' in kwargs and kwargs['encoding'] is not None:
        new_encoding = {}
        for dim in kwargs['encoding'].keys():
            new_dim_encoding = {}
            encoding = kwargs['encoding'][dim]
            if 'chunksizes' in encoding and encoding['chunksizes'] is not None:
                new_dim_encoding['chunks'] = encoding['chunksizes']
            
            if 'complevel' in encoding and encoding['complevel'] is not None:
                shuffle = 2 if encoding['shuffle'] else 0
                new_dim_encoding['compressor'] = zarr.Blosc(cname='zstd', clevel=encoding['complevel'], shuffle=shuffle)
            
            new_encoding[dim] = new_dim_encoding
        new_args['encoding'] = new_encoding
    
    return new_args

args = parser.parse_args()

if args.grid == None and args.unstructured == None:
    print("Either specify a grid or unstructured.")
    exit(1)

if args.zarr and args.netcdf3:
    print("Please specify just one output format.")
    exit(1)

seed = int(numpy.random.rand() * 10000000)
if args.rng_seed is not None:
    seed = args.rng_seed

rng = numpy.random.default_rng(seed)
rng_func = get_random_func(rng, args)

if args.zarr:
    if args.split_count > 1:
        print("Splitting is not supported for zarr stores")
        exit(1)

    generate_file(args, 0, rng_func, {'seed': seed, 'distribution': args.distribution or 'sample(0,1)'})
else:
    if args.verbose:
        print(f"Creating {args.split_count} files...")

    for i in range(0, args.split_count):
        generate_file(args, i, rng_func, {'seed': seed, 'distribution': args.distribution or 'sample(0,1)'})