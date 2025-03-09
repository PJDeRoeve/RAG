class NotSupportedFileFormatError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class DocumentNotYetEmbeddedError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
