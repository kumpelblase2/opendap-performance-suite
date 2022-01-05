import atexit
import os
import subprocess
import logging
import time

SCRIPT_LOCATION = os.path.dirname(os.path.realpath(__file__))

BACKEND_RELATIVE_PATHS = {
    'thredds': 'thredds/dodsC',
    'dars': 'data',
    'hyrax': ''
}

def datapath_for_backend(backend):
    return BACKEND_RELATIVE_PATHS[backend]

def is_container_healthy(container):
    proc = subprocess.run(['docker', 'inspect', "--format='{{json .State.Health.Status}}'", container],
                          capture_output=True)
    output = proc.stdout.decode('utf-8')
    return output.strip().strip("'").strip('"') == 'healthy'


def startup_backend(backend):
    logging.info("Starting %s backend... (This may take a while on first start)", backend)
    try:
        subprocess.run(
            ['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-default.yml', 'up', '-d'],
            capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        error_text = e.stderr.decode('utf-8').strip()
        logging.error("Could not start backend. Exit code: %d, Error: %s", e.returncode, error_text)
        exit(1)
    return backend + '-' + backend + '-backend-1'


def wait_backend(container):
    logging.info("Waiting for backend to be healthy...")
    while True:
        if is_container_healthy(container):
            break
        else:
            time.sleep(1)


def shutdown_backend(backend, _tests):
    logging.info("Shutting down backend...")
    subprocess.run(['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-default.yml', 'exec', backend + '-influx', 'bash', '-c', 'influx query --token telegraf --org telegraf -r \'from(bucket:"telegraf") |> range(start:-1d)\' > /mnt/influx-data/output.csv'], check=True)
    subprocess.run(['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-default.yml', 'exec', backend + '-influx', '/bin/chown', '1000:1000', '/mnt/influx-data/output.csv'], check=True)
    subprocess.run(['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-default.yml', 'down'],
                   check=True, capture_output=True)


def setup_backend(backend, tests, warmup_time=10):
    atexit.register(shutdown_backend, backend, tests)
    container = startup_backend(backend)
    if backend == 'thredds':
        wait_backend(container)
    logging.info("Backend ready.")
    logging.info("Waiting for the backend to be warm...")
    time.sleep(warmup_time)
    logging.info("Warmup done.")
