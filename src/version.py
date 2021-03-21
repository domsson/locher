from enum import Enum

class Version(Enum):
    VERSION_NAME  = "locher"
    VERSION_URL   = "https://github.com/domsson/locher"
    VERSION_MAJOR = 0
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    @classmethod
    def get_name(cls):
        return cls.VERSION_NAME.value

    @classmethod
    def get_version(cls):
        major = str(cls.VERSION_MAJOR.value)
        minor = str(cls.VERSION_MINOR.value)
        patch = str(cls.VERSION_PATCH.value)
        return major + "." + minor + "." + patch

    @classmethod
    def print_name_and_version(cls):
        print(cls.get_name() + " " + cls.get_version())

    @classmethod
    def print_version(cls):
        print(cls.get_version())
        
    @classmethod
    def print_url(cls):
        print(cls.VERSION_URL.value)

    @classmethod
    def print_all(cls):
        cls.print_name_and_version()
        print()
        cls.print_url()
