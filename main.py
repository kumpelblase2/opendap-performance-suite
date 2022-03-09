import argparse
import os
import logging
import time

from backend import setup_backend, datapath_for_backend, append_backend_performance, get_storage_location
from testsuite import run_tests, store_results

class StoreDictKeyPair(argparse.Action):
     def __init__(self, option_strings, dest, nargs=None, **kwargs):
         self._nargs = nargs
         super(StoreDictKeyPair, self).__init__(option_strings, dest, nargs=nargs, **kwargs)
     def __call__(self, parser, namespace, values, option_string=None):
         my_dict = {}
         for kv in values:
             k,v = kv.split("=")
             my_dict[k] = v
         setattr(namespace, self.dest, my_dict)

def get_dataset_files(args, backend_base):
    files = []
    with args.file as dataset_list_file:
        for dataset_entry in dataset_list_file:
            line = dataset_entry.strip()
            if ',' in line:
                files.append([f'{backend_base}/{entry}' for entry in line.split(',')])
            else:
                files.append(f'{backend_base}/{line.strip()}')
    return files

AVAILABLE_BACKENDS = ['thredds', 'hyrax', 'dars']
AVAILABLE_TESTS = {
    'dataset-access': 'Simple accessing test',
    'mean-time': 'Calculate a mean value at a specific point in space over all time values',
    'mean-area': 'Calculate a mean value at a specific point in time the full area'
}
POSSIBLE_TEST_VALUES = list(AVAILABLE_TESTS.keys()) + ['ALL']
SCRIPT_LOCATION = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Test runner for performance evaluation')
parser.add_argument('file', metavar='DATASET_LIST_FILE', type=argparse.FileType('r'),
                    help='The file containing a list of files to run the test on')
parser.add_argument('tests', metavar='TEST', type=str, default=['ALL'], help='The name of the tests to run')
parser.add_argument('test_args', metavar='ARGS', nargs='*', default='', action=StoreDictKeyPair, help='Arguments for the tests')
parser.add_argument('--backend-base', '-H', type=str, default=None, help='The base URL for accessing the data')
parser.add_argument('--backend', '-b', type=str, help='Start the given backend service', default=None)
parser.add_argument('--backend-config', '-c', type=str, help='The configuration used for the backend', default='default')
parser.add_argument('--reruns', '-r', type=int, default=3, help='Amount of reruns of each test to take')
parser.add_argument('--backend-warmup', '-w', type=int, default=10,
                    help='Warmup time (in seconds) for the started backend to settle down')
parser.add_argument('--output', '-o', type=str, default=f'./results/{str(int(time.time()))}',
                    help='Directory to save results to')
parser.add_argument('--verbose', '-v', default=False, help='Enable verbose output', action='store_true')

args = parser.parse_args()

level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y/%m/%d-%H:%M:%S', level=level)

if os.path.exists(args.output) and os.path.isfile(args.output):
    logging.error("Output target exists and is a file. Please specify another output.")
    exit(1)
elif os.path.exists(args.output) and os.path.isdir(args.output):
    if len(os.listdir(args.output)):
        logging.warn("Output directory already contains files so this may overwrite them.")
else:
    os.makedirs(args.output)

backend = args.backend
tests = args.tests.split(',')
if len(tests) == 1 and tests[0] == 'ALL':
    tests = list(AVAILABLE_TESTS.keys())

for test in tests:
    if POSSIBLE_TEST_VALUES.index(test) < 0:
        logging.error("Invalid test %s.", test)
        exit(1)

backend_base = args.backend_base
if backend:
    container_info = setup_backend(backend, tests, args.backend_config, args.backend_warmup)
    if backend_base is None:
        backend_base = f"http://localhost:{container_info['port']}/{datapath_for_backend(backend)}"
        logging.debug("Backend base URL is set to %s", backend_base)

files = get_dataset_files(args, backend_base)

logging.info('Loaded %d datasets to be used for tests.', len(files))

logging.info("Running tests '%s' against '%s'...", ', '.join(tests), backend_base)
result_runs = run_tests(tests, files, args.reruns, args.test_args)
raw_args = [f'{item}={value}' for item, value in args.test_args.items()]
metadata = [args.tests, ','.join(raw_args)]
if backend:
    metadata += [backend, args.backend_config, get_storage_location()]

store_results(result_runs, args.output, metadata=metadata)
if backend:
    append_backend_performance(args.output, backend)
logging.info("Written results to %s.", args.output)
