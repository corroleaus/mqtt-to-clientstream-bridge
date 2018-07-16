class ConfigException(Exception):
    def __init__(self, msg, orig_exception=None):
        super(ConfigException, self).__init__(
            msg + (": %s" % orig_exception if orig_exception else ""))
        self.orig_exception = orig_exception
