class CohereError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg


class OpenAIError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg
