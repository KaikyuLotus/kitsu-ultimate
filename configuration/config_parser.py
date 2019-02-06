from exceptions.bad_configuration_file_format import BadConfigurationFileFormat
from configuration import configuration


def parse_config_file(file_name):
    config = {}
    for line in open(file_name).readlines():
        if "=" not in line or line.startswith("="):
            raise BadConfigurationFileFormat(file_name)

        # rstrip needed to remove final newline
        # we need to split only the first =, the value can contain other =
        key, value = line.rstrip().split("=", maxsplit=1)

        # we just need to check the first word before the dot
        # and we need the rest of the string as a singe value if needed
        tree = key.split(".", maxsplit=1)
        if len(tree) > 1:  # if there's something with more words
            if tree[0] in ["test", "dev", "prod"]:  # check if it's an env
                if tree[0] == configuration.get_current_env():  # check if it's current env
                    key = tree[1]  # remove the root word
                else:  # we don't need this var
                    continue
        # save the var
        config[key] = value
    return config
