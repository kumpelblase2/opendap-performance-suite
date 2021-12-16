import logging
import time

import scripts.simple
import scripts.mean

TESTS = {
    'dataset-access': scripts.simple.SimpleTest(),
    'mean': scripts.mean.MeanTest()
}


def run_test(test, files, reruns=3):
    return TESTS[test].run(files, reruns)


def run_tests(tests, files, reruns=3):
    start_time = time.time()
    results = {}
    for test in tests:
        results[test] = run_test(test, files, reruns)

    test_time = time.time() - start_time
    logging.info("Tests finished in %d seconds.", int(test_time))
    return results


def store_results(results, output_file):
    with output_file as f:
        f.write(';'.join(['Test', 'Dataset', 'Step', 'Run', 'Time']) + '\n')
        for test in results.keys():
            test_data = results[test]
            for dataset in test_data:
                for i, run in enumerate(test_data[dataset], start=1):
                    for key in run.keys():
                        f.write(';'.join([test, dataset, key, str(i), str(run[key])]) + '\n')
