from abc import abstractmethod, ABC
from typing import Generator, Iterable, List, Type, TypeVar

from aiohttp import ClientSession
from tenacity import retry, stop_after_attempt, wait_random


CustomError = TypeVar("CustomError", bound=Exception)


class BaseEmbeddingClass(ABC):
    def __init__(self, session: ClientSession, key: str):
        if not isinstance(session, ClientSession):
            raise TypeError("'session' should be a ClientSession object")
        if not isinstance(key, str):
            raise TypeError("'key' should be a str object")

        self.headers: dict = {"Authorization": f"Bearer {key}"}
        self.session: ClientSession = session

    @abstractmethod
    async def embed(self, docs: Iterable[str]):
        pass

    @retry(stop=stop_after_attempt(3), wait=wait_random(), reraise=True)
    async def _post_json(
        self, url: str, body: dict, headers: dict, error: Type[CustomError]
    ) -> dict:
        """Send a POST request to the specified URL through the 'session' attribute"""
        async with self.session.post(url=url, json=body, headers=headers) as resp:
            try:
                resp.raise_for_status()
                resp_json: dict = await resp.json()
                return resp_json
            except Exception as e:
                raise error(str(e)) from e

    def _validate_docs(self, docs: Iterable[str]) -> None:
        """Verify the format and contents of 'docs'"""
        if (
            not isinstance(docs, Iterable)
            or len(docs) == 0
            or not all(isinstance(s, str) for s in docs)
        ):
            raise TypeError(
                "'docs' should be an non-empty Iterable of str objects"
            )
        return

    def _partition_docs(
        self, docs: Iterable[str], limit: int
    ) -> Generator[List[str], None, None]:
        """Partition docs into smaller sublists to avoid running into API token limits"""
        for i in range(0, len(docs), limit):
            partition = docs[i : i + limit]
            yield partition
