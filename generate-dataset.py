import xarray
import numpy
import argparse

SPLIT_OPTIONS=['time', 'area']

parser = argparse.ArgumentParser(description='Generate synthetic datasets for testing')

parser.add_argument('file', metavar='OUTPUT', type=str, help='The file to write the output to')
parser.add_argument('--time-values', '-t', type=int, default=365, help='How many time entries')
parser.add_argument('--vars', '-V', type=int, default=1, help='Amount of variables to create')
parser.add_argument('--grid', '-g', type=float, help='Use a normal grid with the given resolution')
parser.add_argument('--unstructured', '-u', type=int, help='Use an unstructured grid with the given amount of cells')
parser.add_argument('--split', '-s', type=str, choices=SPLIT_OPTIONS, default='time', help='Along where to split files')
parser.add_argument('--split-count', '-f', type=int, default=1, help='Amount of files to split int')
parser.add_argument('--chunking', '-c', type=str, help='Chunking in the format "<var>=<size>,<var>=<size>,..."')
parser.add_argument('--compression', '-C', type=int, help='Compression level for variables')
parser.add_argument('--rng-seed', '-r', type=int, help='Seed for randomizer')
parser.add_argument('--netcdf3', '-3', default=False, action='store_true', help='Output a NetCDF3 file')
parser.add_argument('--verbose', '-v', default=False, action='store_true')

def generate_file(args, index, rng, seed):
    if args.verbose:
        print(f"Generating file {index}...")
    grid = generate_grid(args, index)
    vars = [generate_var(grid, rng) for i in range(0, args.vars)]
    if len(grid) == 3:
        coords = {
            'time': ('time', grid[0]),
            'longitude': ('longitude', grid[1]),
            'latitude': ('latitude', grid[2]),
        }
    else:
        coords = {
            'time': ('time', grid[0]),
            'ncells': ('ncells', grid[1])
        }

    var_dict = {}
    for i, var in enumerate(vars):
        var_dict[f"var_{i}"] = (coords.keys(), var)

    chunking = parse_chunking(args.chunking) if args.chunking is not None else None
    encoding = {}
    for i in range(0, len(vars)):
        var_name = f'var_{i}'
        encode_vars = {}
        if args.compression is not None:
            encode_vars = encode_vars | dict(zlib=True, complevel=args.compression)
        
        if chunking is not None:
            encode_vars = encode_vars | dict(chunksizes=chunking)

        if len(encode_vars.keys()) > 0:
            encoding[var_name] = encode_vars
        

    ds = xarray.Dataset(data_vars=var_dict, coords=coords, attrs=dict(seed=seed))
    kwargs = {}
    if args.netcdf3:
        kwargs['format'] = 'NETCDF3_CLASSIC'

    if len(encoding.keys()) > 0:
        kwargs['encoding'] = encoding
    
    if args.split == 'time':
        kwargs['unlimited_dims'] = ['time']
    elif args.grid is not None:
        kwargs['unlimited_dims'] = ['longitude', 'latitude']
    
    ds.to_netcdf(f"{args.file}_{index}.nc", **kwargs)

def generate_grid(args, index):
    if args.grid is not None:
        resolution = args.grid
        if args.split == 'time':
            longitude = numpy.arange(0, 360, resolution)
            latitude = numpy.arange(-90, 90, resolution)
            time = generate_time_slice(args.time_values, args.split_count)
            return [time, longitude, latitude]
        elif args.split == 'area':
            time = numpy.arange(args.time_values)
            if args.split_count % 2 != 1:
                print("Split count needs to be a multiple of two when using area")
                exit(1)
            
            [longitude, latitude] = generate_area(resolution, args.split_count, index)
            return [time, longitude, latitude]

    else:
        if args.split == 'time':
            cells = args.unstructured
            time = generate_time_slice(args.time_values, args.split_count)
            cells = numpy.arange(cells)
            return [time, cells]
        elif args.split == 'area':
            cells_per_file = args.unstructured / args.split_count
            time = numpy.arange(args.time_values)
            cells = numpy.arange(index * cells_per_file, (index + 1) * cells_per_file)
            return [time, cells]


def generate_time_slice(values, splits):
    time_per_file = int(values / splits)
    return numpy.arange(i * time_per_file, (i + 1) * time_per_file)

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

def generate_var(grid, rng):
    if len(grid) == 3:
        [time, longitude, latitude] = grid
        return rng.random((len(time), len(longitude), len(latitude)))
    else:
        [time, ncells] = grid
        return rng.random((len(time), len(ncells)))

def parse_chunking(string):
    var_chunks = string.split(',')
    key_value_arrays = [var.split('=') for var in var_chunks]
    chunking = {key_value[0]: key_value[1] for key_value in key_value_arrays}
    return (int(chunking['time']), int(chunking['longitude']), int(chunking['latitude']))

args = parser.parse_args()

if args.grid == None and args.unstructured == None:
    print("Either specify a grid or unstructured.")
    exit(1)

seed = int(numpy.random.rand() * 10000000)
if args.rng_seed is not None:
    seed = args.rng_seed

rng = numpy.random.default_rng(seed)

if args.verbose:
    print(f"Creating {args.split_count} files...")

for i in range(0, args.split_count):
    generate_file(args, i, rng, seed)