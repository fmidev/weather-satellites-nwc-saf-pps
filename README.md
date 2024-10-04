
# Container recipe for PPS

---
*NOTE*

Work in progress.
---

The aim of this container recipe is to build NWC SAF PPS with some
additions so that a incoming Posttroll message triggers conversion of
data to Level 1C and eventually run the PPS processing.

## Static auxiliary data

The static auxiliary data from NWC SAF should be pre-extracted to the
proper directory (`$DATA_DIR/static/`).

## NWP data

Up-to-date NWP data should be placed in `$DATA_DIR/import/NWP_data` by
an external system.

## Satellite data

The location of satellite data are taken from the incoming Posttroll
message. The full path should be accessible within the container. So
if the satellite data are in `/data/polar/avhrr/ears/l1b` the
directory should be mounted to the container with the exact same path.

This data are then converted to the L1c format PPS requires before
passing it to PPS.

## Configuration

Configuration should be mounted to the internal `/config` directory.

### `/config/env-variables`

This file contains the PPS environment variables. Which are
plenty. The only that might need modification is `DATA_DIR`, which
should point to the parent directory of `export/`, `import/`,
`intermediate/`, `static/` and `tmp/` directories.

### `run_pps.yaml`

The container configuration is simple:
* subscriber settings for Posttroll
* (internal) output location of Level 1C files
* which PPS command to use for processing

```yaml
subscriber:
  nameserver: False
  addresses: "<hostname>:<port number>"
l1c_out_dir: /data/polar/avhrr/ears/l1c
pps_command: ppsRunAllParallel_inclCMaProb.py
```

The PPS product output will be placed in `$DATA_DIR/export/`.

## Compilation with Podman

Place `pps_v2021_patch3_conda_packages.tar` in the source directory
and run

```bash
podman build -t pps .
```

## Running with Podman

Assuming the `$DATA_DIR` directory is under `/data` and the
configuration files are placed in `/config/polar-avhrr/pps`, use this
to run the container:

```bash
podman run \
    --rm \
    -v /data:/data:Z \
    -v /config/polar-avhrr/pps:/config:Z \
    pps
```
