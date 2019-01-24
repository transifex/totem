class StringBuilder:
    """A utility class that can be used for the lazy creation of line-based
    report strings.
    """

    def __init__(self):
        self.strings = []

    def add(self, string: str = ''):
        """Add a new line."""
        self.strings.append(string)

    def render(self) -> str:
        """Return a multi-line string with all the strings."""
        return '\n'.join(self.strings)
