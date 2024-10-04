#!/usr/bin/env python

def main():
    """Listen to messages and process them."""
    import glob
    import os
    import sys
    import yaml

    from posttroll.subscriber import Subscribe

    with open(sys.argv[1], "r") as fid:
        config = yaml.load(fid, Loader=yaml.SafeLoader)

    existing_file_pattern = config.get("existing_file_pattern", "*.nc")
    product_pattern = os.path.join(os.environ["DATA_DIR"], "export", existing_file_pattern)
    old_files = glob.glob(product_pattern)

    sub_config = config["subscriber"]
    with Subscribe(**sub_config) as sub:
        _process_messages(sub, config)

    # fname = "/data/l1b/hrpt_metop03_20210310_1911_12143.l1b"
    # l1c_fname = run_l1c4pps(fname, "avhrr", config["l1c_out_dir"])
    # l1c_fname = os.path.join(config["l1c_out_dir"], "S_NWC_avhrr_metopc_00000_20210310T1911174Z_20210310T1926396Z.nc")
    l1c_fname = run_l1c4pps(msg.data["uid"], "avhrr", config["l1c_out_dir"])
    run_pps(l1c_fname, config["pps_command"])

    new_files = glob.glob(product_pattern)
    print("New PPS product files:", set(new_files) - set(old_files))


def _process_messages(sub, config):
    for msg in sub.recv(1):
        if msg is None:
            continue
        if msg_in.type == "file" and "uid" in msg_in.data:
            l1c_fname = run_l1c4pps(msg_in.data["uid"], msg_in.data["sensor"], config["l1c_out_dir"])
            pps_fnames = run_pps(l1c_fname, config["pps_command"])
            # PPS has post-hooks for publishing the products, so no need for that here


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
    # cmd = [pps_command, "--no_cmic", "--anglesfile", fname]
    cmd = [pps_command, "--anglesfile", fname]
    run_popen(cmd)


def run_popen(cmd):
    """Run a command with Popen."""
    from subprocess import PIPE, Popen

    process = Popen(cmd, shell=False, stderr=PIPE, stdout=PIPE)
    process.wait()
    output, error = process.communicate()
    print(output)
    print()
    print(error)


if __name__ == "__main__":
    main()


def publish_pps_data(pps_fnames, msg_in, config):
    """Publish a message with metadata on the processed PPS data."""
    # Move this to a PPS post-hook
    from posttroll.message import Message
    from posttroll.publisher import Publish

    pub_config = config["publisher"].copy()
    publish_topic = pub_config.pop("publish_topic")
    with Publish("run_pps", **pub_config) as pub:
        msg_data = {
            "dataset": [
                {"uri": f, "uid": os.path.basename(f)} for f in pps_fnames
            ],
            "sensor": msg_in.data["sensor"],
            "platform_name": msg_in.data["platform_name"],
            "start_time": msg_in.data["start_time"],
            "end_time": msg_in.data["end_time"]
        }
        msg_out = Message(publish_topic, "dataset", msg_data)
        pub.send(msg_out)
