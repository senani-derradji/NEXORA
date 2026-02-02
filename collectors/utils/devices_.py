import yaml, os


class OpenMetricsInformer:

    @staticmethod
    def _load_devices(devices_file):

        if os.path.exists(devices_file):
            with open(devices_file) as f:
                devices = yaml.safe_load(f)["devices"]
        else:
            devices = None

        return devices
