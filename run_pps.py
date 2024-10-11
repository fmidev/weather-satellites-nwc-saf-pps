#!/usr/bin/env python

import glob
import os
import sys
import yaml

from posttroll.message import Message
from posttroll.publisher import Publish
from posttroll.subscriber import Subscribe


def main():
    """Listen to messages and process them."""
    with open(sys.argv[1], "r") as fid:
        config = yaml.load(fid, Loader=yaml.SafeLoader)

    _process_messages(config)
    # _process_file(config)


def _process_messages(config):
    sub_config = config["subscriber"]
    with Subscribe(**sub_config) as sub:
        for msg in sub.recv(1):
            if msg is None:
                continue
            _process_message(msg, config)


def _process_message(msg, config):
    if not (msg.type == "file" and "uid" in msg.data):
        return

    old_files = _get_existing_product_files(config)
    l1c_fname = run_l1c4pps(msg.data["uid"], msg.data["sensor"], config["l1c_out_dir"])
    pps_fnames = run_pps(l1c_fname, config["pps_command"])
    new_files = set(_get_existing_product_files(config)) - set(old_files)

    if new_files:
        publish_pps_data(new_files, msg.data, config)


def _process_file(config):
    old_files = _get_existing_product_files(config)

    fname = "/data/l1b/hrpt_metop03_20210310_1911_12143.l1b"
    l1c_fname = run_l1c4pps(fname, "avhrr", config["l1c_out_dir"])
    run_pps(l1c_fname, config["pps_command"])

    new_files = set(_get_existing_product_files(config)) - set(old_files)
    if new_files:
        msg_data = {"sensor": "avhrr", "platform_name": "Metop-B", "start_time": "start_time", "end_time": "end_time"}
        publish_pps_data(new_files, msg_data, config)


def _get_existing_product_files(config):
    existing_file_pattern = config.get("existing_file_pattern", "*.nc")
    product_pattern = os.path.join(os.environ["DATA_DIR"], "export", existing_file_pattern)
    return glob.glob(product_pattern)


def run_l1c4pps(fname, instrument, out_dir):
    """Run conversion to L1C."""
    processor = _get_processor(instrument)
    return processor([fname], out_dir)


def _get_processor(instrument):
    if instrument == "avhrr":
        from level1c4pps.avhrr2pps_lib import process_one_scene
    elif instrument == "mersi":
        from level1c4pps.mersi22pps_lib import process_one_scene
    elif instrument == "viirs":
        from level1c4pps.viirs2pps_lib import process_one_scene
    else:
        raise ValueError(f"Unsupported instrument {instrument}")
    return process_one_scene


def run_pps(fname, pps_command):
    """Run PPS processing for the given file."""
    cmd = [pps_command, "--anglesfile", fname]
    run_popen(cmd)


def run_popen(cmd):
    """Run a command with Popen."""
    from subprocess import PIPE, Popen, STDOUT

    with Popen(cmd, shell=False, stderr=STDOUT, stdout=PIPE) as process:
        while True:
            stdout = process.stdout.read1().decode("utf-8")
            print(stdout, flush=True, end="")
            if process.poll() is not None:
                break


def publish_pps_data(pps_fnames, msg_data, config):
    """Publish a message with metadata on the processed PPS data."""
    pub_config = config["publisher"].copy()
    publish_topic = pub_config.pop("publish_topic")
    with Publish("run_pps", **pub_config) as pub:
        msg_data = {
            "dataset": [
                {"uri": f, "uid": os.path.basename(f)} for f in pps_fnames
            ],
            "sensor": msg_data["sensor"],
            "platform_name": msg_data["platform_name"],
            "start_time": msg_data["start_time"],
            "end_time": msg_data["end_time"]
        }
        msg_out = Message(publish_topic, "dataset", msg_data)
        print("Publishing message:", msg_out)
        pub.send(str(msg_out))


if __name__ == "__main__":
    main()
