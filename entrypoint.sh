#!/usr/bin/bash

source /opt/conda/.bashrc

micromamba activate

source /config/env-variables

/usr/bin/run_pps.py /config/run_pps.yaml
