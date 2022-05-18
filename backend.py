import atexit
import os
import subprocess
import logging
import time
import shutil

SCRIPT_LOCATION = os.path.dirname(os.path.realpath(__file__))

BACKEND_RELATIVE_PATHS = {
    'thredds': 'thredds/dodsC',
    'dars': 'data',
    'hyrax': 'opendap'
}

BACKEND_PORTS = {
    'thredds': 8080,
    'dars': 80,
    'hyrax': 8080
}

query = """
from(bucket:"telegraf") 
|> range(start:-1d)
|> filter(fn: (r) => 
    contains(value: r._field, set: ["active", "io_time", "read_bytes", "reads", "usage_iowait", "usage_system", "usage_user"])
)
|> keep(columns: ["_time","_value","_field","_measurement", "cpu", "name"])
"""

def mount_volume(path):
    subprocess.run(['docker', 'volume', 'create', '--name=data_files', '--opt', 'type=none', '--opt', f'device={path}', '--opt', 'o=bind'], capture_output=True)

def unmount_volume():
    subprocess.run(['docker', 'volume', 'rm', 'data_files'], capture_output=True)

def datapath_for_backend(backend):
    return BACKEND_RELATIVE_PATHS[backend]

def is_container_healthy(container):
    proc = subprocess.run(['docker', 'inspect', "--format='{{json .State.Health.Status}}'", container],
                          capture_output=True)
    output = proc.stdout.decode('utf-8')
    return output.strip().strip("'").strip('"') == 'healthy'


def startup_backend(backend, config):
    logging.info("Starting %s backend (config: %s)... (This may take a while on first start)", backend, config)
    try:
        subprocess.run(
            ['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-{config}.yml', 'up', '-d'],
            capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        error_text = e.stderr.decode('utf-8').strip()
        logging.error("Could not start backend. Exit code: %d, Error: %s", e.returncode, error_text)
        exit(1)
    internal_port = BACKEND_PORTS[backend]
    container_name = backend + '-' + config + '-backend-1'
    try:
        format_ = '{{(index (index .NetworkSettings.Ports "' + str(internal_port) + '/tcp") 0).HostPort}}'
        proc = subprocess.run(['docker', 'inspect', f'--format=\'{format_}\'', container_name], capture_output=True, check=True)
        external_port = int(proc.stdout.decode('utf-8').strip().strip("'").strip('"'))
    except subprocess.CalledProcessError as e:
        error_text = e.stderr.decode('utf-8').strip()
        logging.error("Could not determine port of backend. Exit code: %d, Error: %s", e.returncode, error_text)
        exit(1)
    
    return {
        'container': container_name,
        'port': external_port
    }


def wait_backend(container):
    logging.info("Waiting for backend to be healthy...")
    while True:
        if is_container_healthy(container):
            break
        else:
            time.sleep(1)


def shutdown_backend(backend, config, _tests):
    logging.info("Shutting down backend...")
    subprocess.run(['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-{config}.yml', 'exec', config + '-influx', 'bash', '-c', f'influx query --token telegraf --org telegraf -r \'{query}\' > /mnt/influx-data/output.csv'], check=True)
    subprocess.run(['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-{config}.yml', 'exec', config + '-influx', '/bin/chown', '1000:1000', '/mnt/influx-data/output.csv'], check=True)
    subprocess.run(['docker-compose', '-f', f'{SCRIPT_LOCATION}/tests/{backend}/docker-compose-{config}.yml', 'down'],
                   check=True, capture_output=True)


def setup_backend(backend, tests, config='default', warmup_time=10):
    atexit.register(shutdown_backend, backend, config, tests)
    container_info = startup_backend(backend, config)
    if backend == 'thredds':
        wait_backend(container_info['container'])
    logging.info("Backend ready.")
    logging.info("Waiting for the backend to be warm...")
    time.sleep(warmup_time)
    logging.info("Warmup done.")
    return container_info


def append_backend_performance(output_dir, backend):
    shutil.copyfile(f'tests/{backend}/measurement-output/output.csv', os.path.join(output_dir, 'monitor.csv'))


def get_storage_location():
    proc = subprocess.run(['docker', 'volume', 'inspect', '--format=\'{{ .Options.device }}\'', 'data_files'], capture_output=True, check=True)
    output = proc.stdout.decode('utf-8')
    return output.strip()