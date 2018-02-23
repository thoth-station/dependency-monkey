class EcosystemNotSupportedError(Exception):
    """Exception raised if a Ecosystem is not supported.

    Attributes:
        name -- name of the ecosystem
    """

    def __init__(self, name):
        self.name = name
        self.message = "Ecosystem {} is not supported".format(name)

    def str(self):
        return self.message


ECOSYSTEM = ['pypi']
