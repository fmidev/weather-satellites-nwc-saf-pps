#!/usr/bin/bash

source /opt/conda/.bashrc
source /config/env-variables

micromamba activate

/usr/bin/run_pps.py -c /config/run_pps.yaml

