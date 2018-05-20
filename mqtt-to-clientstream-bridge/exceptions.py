class ConfigException(Exception):
    def __init__(self, msg, orig_exception):
        super(ConfigException, self).__init__(msg + (": %s" % orig_exception))
        self.orig_exception = orig_exception