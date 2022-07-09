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

## How to run

Die Testsuite kann sowohl auf einen im Docker-Container laufenden Server gerichtet werden, als auch auf einen anderweitig gestarteten Server. Zunächst wird hier ein externer Server betrachtet.

Mit `python main.py -h` erhält man eine Übersicht zu den Parametern der Test-Suit:
```
usage: main.py [-h] [--backend-base BACKEND_BASE] [--backend BACKEND] [--backend-config BACKEND_CONFIG] [--reruns RERUNS] [--backend-warmup BACKEND_WARMUP] [--output OUTPUT] [--volume VOLUME] [--verbose]
               DATASET_LIST_FILE TEST [ARGS ...]

Test runner for performance evaluation

positional arguments:
  DATASET_LIST_FILE     The file containing a list of files to run the test on
  TEST                  The name of the tests to run
  ARGS                  Arguments for the tests

options:
  -h, --help            show this help message and exit
  --backend-base BACKEND_BASE, -H BACKEND_BASE
                        The base URL for accessing the data
  --backend BACKEND, -b BACKEND
                        Start the given backend service
  --backend-config BACKEND_CONFIG, -c BACKEND_CONFIG
                        The configuration used for the backend
  --reruns RERUNS, -r RERUNS
                        Amount of reruns of each test to take
  --backend-warmup BACKEND_WARMUP, -w BACKEND_WARMUP
                        Warmup time (in seconds) for the started backend to settle down
  --output OUTPUT, -o OUTPUT
                        Directory to save results to
  --volume VOLUME, -V VOLUME
                        Directory with data files to mount
  --verbose, -v         Enable verbose output
```

Es muss entweder `--backened` oder `--backend-base` spezifiziert werden; `--backend` bezeichnet den Namen des Backends, welches von der Suite in Docker gestartet werden soll, `--backend-base` den Basis-HTTP-URL zur OPeNDAP Schnittstelle des externen Servers, z.B. `http://10.10.124.215:8080/thredds/dodsC` bei einem THREDDS Server.

`DATASET_LIST_FILE` ist eine Datei, die eine Liste an Datendateien enthält, die von den Tests der Testsuite benutzt werden sollen. Es wird pro Zeile eine Daten-Datei erwartet. Diese werden jeweils mit der Basis-URL verknüpft, um die vollständige URL für die entsprechende Datei zu bekommen. Falls mehrere Dateien als eine Datei über `open_mfdataset` geöffnet werden sollen, können diese Dateien in der gleichen Zeile angeführt werden. Diese müssen dann durch ein Komma von einander getrennt werden, `path/test.nc,path/other.nc` as Beispiel.

`TEST` ist eine Liste von Tests, die ausgeführt werden sollen. Werden keine Tests angegeben, werden alle ausgeführt.

Um also auf einem externen THREDDS Server die Evaluation durchgeführt werden, so könnte der Aufruf wie folgt aussehen:
```shell
python main.py --backend-base "http://10.10.124.215:8080/thredds/dodsC" tests/dataset.txt mean-time
```
Die Ergebnisse werden dann in eine Datei mit dem Namen `timings.csv` geschrieben, die in einem neuen Ordner mit den aktuellem Timestamp eingelegt wurde.

Um ein Docker-basiertes Backend zu starten, wird statt `--backend-base` hier `--backend` mit dem entsprechendem Namen genutzt. Um `dars` im Container zu starten, würde der volle Befehl also wir folgt aussehen:
```shell
python main.py --backend dars tests/dataset.txt mean
```
Die Container benötigen jedoch vorher ein Volume in dem die Daten vorhanden sind. Dazu sollte entweder vorher mit `docker volume` eine Volume erstellt werden, das die Daten enthält. Um etwa die Daten aus einem lokalen Order `/mnt/data/netcdf-files` einzubinden, würde dieser wie folgt aussehen:
```shell
docker volume create --name data_files --opt type=none --opt device=/mnt/data/netcdf-files --opt o=bind
```
Der Name muss dabei `data_files` sein, damit er von den Containern erkannt wird.
Alternative kann auch die Option `--volume` beim Aufruf angegeben werden, wodurch die mitgegebene Pfad automatisch vorher als Volume erstellt wird. Das Volume wird dann auch automatisch nach dem Test wieder gelöscht.

Um verschiedene Konfiguration von einem Server zu testen gibt es die Option `--backend-config`, welche die entsprechende `docker-compose.yml` Datei zum Starten des Servers auswählt.

## Datensatzgenerierung

Das Tool `generate-dataset.py` ermöglicht das Erstellen von identischen Daten-Dateien nach einer vorgegebenen Struktur. Je nach vorgabe können NetCDF3, NetCDF4, oder Zarr Daten erstellt werden mit unterschiedlichem Chunking, Variablenanzahl, oder anderen Eigenschaften. Die komplette Liste mit Option sieht wie folgt aus:
```
usage: generate-dataset.py [-h] [--time-values TIME_VALUES] [--vars VARS] [--grid GRID] [--unstructured UNSTRUCTURED] [--split {time,area}] [--split-count SPLIT_COUNT] [--chunking CHUNKING]
                           [--compression COMPRESSION] [--rng-seed RNG_SEED] [--no-shuffle] [--distribution DISTRIBUTION] [--netcdf3] [--height HEIGHT] [--zarr] [--verbose] [--datetime]
                           OUTPUT

Generate synthetic datasets for testing with 2 (unstructured) or 3 (grid) dimensions with one or more variables.

positional arguments:
  OUTPUT                The name of the file to write the output to. When multiple files will generated, the files will be called "<name>_0", "<name>_1", etc.

options:
  -h, --help            show this help message and exit
  --time-values TIME_VALUES, -t TIME_VALUES
                        How many time entries
  --vars VARS, -V VARS  Amount of variables to create
  --grid GRID, -g GRID  Use a normal grid with the given resolution
  --unstructured UNSTRUCTURED, -u UNSTRUCTURED
                        Use an unstructured grid with the given amount of cells
  --split {time,area}, -s {time,area}
                        Along where to split files
  --split-count SPLIT_COUNT, -f SPLIT_COUNT
                        Amount of files to split int
  --chunking CHUNKING, -c CHUNKING
                        Chunking in the format "<var>=<size>,<var>=<size>,..."
  --compression COMPRESSION, -C COMPRESSION
                        Compression level for variables
  --rng-seed RNG_SEED, -r RNG_SEED
                        Seed for randomizer
  --no-shuffle, -S      Disable shuffling when compressing data
  --distribution DISTRIBUTION, -d DISTRIBUTION
                        Which distribution model to use for random variables. Format is "<distribution>(<arg1>, <arg2>,...)"
  --netcdf3, -3         Output a NetCDF3 file instead of a NetCDF4
  --height HEIGHT, -H HEIGHT
                        Add a fourth dimension - height - with the given amount of entries
  --zarr, -z            Output a zarr store
  --verbose, -v
  --datetime, -D        Use datetime values instead of int for time dimension
```

Um beispielsweise eine NetCDF4 Datei zu erstellen die Compression-Level 6, ein reguläres Grid mit Auflösung von 0.25Grad und ein Chunking von `time=1,longitude=1440,latitude=720` besitzt, kann folgender Befelh verwendet werden:
```
python generate-dataset.py --time-values 720 --grid 0.25 --compression 6 --chunking "time=1,longitude=1440,latitude=720" my-dataset
```

Bei keiner Angabe eines Seeds für den RNG wir ein neuer Seed verwendet, welcher auch in die generierte Datei geschrieben wird. Um nun die gleiche Datei erneut zu generieren wird der gleiche Aufruf verwendet unter der Angabe von dem Seed durch `--rng-seed`.

Es ist auch möglich geteilte Datensätze zu erstellen, in dem etwa jede Datei ein Jahr an Daten beinhaltet. Dazu wird `--split` und `--split-count` verwendet. `--split` gibt an, entlang welcher Dimension geteilt werden soll, zeitlich oder räumlich, und `--split-count` dann wie viele Dateien am Ende entstehen sollen. Falls, zum Beispiel, jede Datei ein Jahr an Daten beinhalten soll und insgesammt fünf Jahre an Daten generiert werden sollen, dann wäre der Aufruf wie folgt:
```
python generate-dataset.py --time-values 1825 --split time --split-count 5 ...
```