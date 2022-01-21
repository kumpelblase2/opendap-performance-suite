import argparse
import os
import logging
import time

from backend import setup_backend, datapath_for_backend, append_backend_performance
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
parser.add_argument('--reruns', '-r', type=int, default=3, help='Amount of reruns of each test to take')
parser.add_argument('--backend-warmup', '-w', type=int, default=10,
                    help='Warmup time (in seconds) for the started backend to settle down')
parser.add_argument('--output', '-o', type=argparse.FileType('w'), default=f'results-{str(int(time.time()))}.csv',
                    help='File to write recorded data to')
parser.add_argument('--verbose', '-v', default=False, help='Enable verbose output', action='store_true')

args = parser.parse_args()

level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y/%m/%d-%H:%M:%S', level=level)

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
    container_info = setup_backend(backend, tests, args.backend_warmup)
    if backend_base is None:
        backend_base = f"http://localhost:{container_info['port']}/{datapath_for_backend(backend)}"
        logging.debug("Backend base URL is set to %s", backend_base)

files = []
with args.file as dataset_list_file:
    for dataset in dataset_list_file:
        files.append(f'{backend_base}/{dataset.strip()}')

logging.info('Loaded %d datasets to be used for tests.', len(files))

logging.info("Running tests '%s' against '%s'...", ', '.join(tests), backend_base)
result_runs = run_tests(tests, files, args.reruns, args.test_args)
metadata = [args.tests, args.test_args]
if backend:
    metadata += [backend]

store_results(result_runs, args.output, metadata=metadata)
if backend:
    append_backend_performance(args.output, backend)
logging.info("Written results to %s.", args.output.name)
