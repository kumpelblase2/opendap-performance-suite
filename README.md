# THREDDS Performance Suite

Eine Test-Suite zum Evaluieren der Performance von THREDDS und anderen OPeNDAP Systemen.

## Tests

Tests befinden sich hauptsächlich im `/scripts` Ordner, sind aber an mehreren Stellen konfiguriert:
- `main.py` für die existenzprüfung
- `testsuite.py` für das Mapping Name <-> Script

## Backends

Aktuell sind 3 Backends konfiguriert:
- THREDDS
- Hyrax
- dars

Die Backends sind jeweils mit den gleichen Daten eingestellt und akkumulieren Systeminformationen in eine InfluxDB, die jeweils mit gestartet wird.
Die Container der Backends sind insofern erweitert, sodass Telegraf mit der Server Software gestartet wird, um die Informationen an InfluxDB zu senden.


## Datasets

## How to run

Die Testsuite kann sowohl auf einen im Docker-Container laufenden Server gerichtet werden, als auch auf einen anderweitig gestarteten Server. Zunächst wird hier ein externer Server betrachtet.

Mit `python main.py -h` erhält man eine Übersicht zu den Parametern der Test-Suit:
```
usage: main.py [-h] [--backend-base BACKEND_BASE] [--backend BACKEND] [--reruns RERUNS] [--backend-warmup BACKEND_WARMUP] [--output OUTPUT] [--verbose] DATASET_LIST_FILE [TEST ...]

Test runner for performance evaluation

positional arguments:
  DATASET_LIST_FILE     The file containing a list of files to run the test on
  TEST                  The name of the tests to run

options:
  -h, --help            show this help message and exit
  --backend-base BACKEND_BASE, -H BACKEND_BASE
                        The base URL for accessing the data
  --backend BACKEND, -b BACKEND
                        Start the given backend service
  --reruns RERUNS, -r RERUNS
                        Amount of reruns of each test to take
  --backend-warmup BACKEND_WARMUP, -w BACKEND_WARMUP
                        Warmup time (in seconds) for the started backend to settle down
  --output OUTPUT, -o OUTPUT
                        File to write recorded data to
  --verbose, -v         Enable verbose output
```

Es muss entweder `--backened` oder `--backend-base` spezifiziert werden; `--backend` bezeichnet den Namen des Backends, welches von der Suite in Docker gestartet werden soll, `--backend-base` den Basis-HTTP-URL zur OPeNDAP Schnittstelle des externen Servers, z.B. `http://10.10.124.215:8080/thredds/dodsC` bei einem THREDDS Server.

`DATASET_LIST_FILE` ist eine Datei, die eine Liste an Datendateien enthält, die von den Tests der Testsuite benutzt werden sollen. Diese werden jeweils mit der Basis-URL verknüpft, um die vollständige URL für die entsprechende Datei zu bekommen.

`TEST` ist eine Liste von Tests, die ausgeführt werden sollen. Werden keine Tests angegeben, werden alle ausgeführt.

Um also auf einem externen THREDDS Server die Evaluation durchgeführt werden, so könnte der Aufruf wie folgt aussehen:
```shell
python main.py --backend-base "http://10.10.124.215:8080/thredds/dodsC" tests/dataset.txt mean
```
Die Ergebnisse werden dann in eine Datei mit dem Namen `results-X.csv` geschrieben, wobei mit `X` der Timestamp angegeben ist.

Um ein Docker-basiertes Backend zu starten, wird statt `--backend-base` hier `--backend` mit dem entsprechendem Namen genutzt. Um `dars` im Container zu starten, würde der volle Befehl also wir folgt aussehen:
```shell
python main.py --backend dars tests/dataset.txt mean
```
Die Container benötigen jedoch vorher ein Volume in dem die Daten vorhanden sind. Dazu sollte vorher mit `docker volume` eine Volume erstellt werden, das die Daten enthält. Um etwa die Daten aus einem lokalen Order `/mnt/data/netcdf-files` einzubinden, würde dieser wie folgt aussehen:
```shell
docker volume create --name data_files --opt type=none --opt device=/mnt/data/netcdf-files --opt o=bind
```
Der Name muss dabei `data_files` sein, damit er von den Containern erkannt wird.