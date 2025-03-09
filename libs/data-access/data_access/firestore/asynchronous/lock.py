import asyncio
import json
import logging
from datetime import timedelta
from typing import List
from uuid import UUID

from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore
from tenacity import retry, stop_after_attempt, wait_random

from data_access.firestore.asynchronous import schemas
from data_access.utils import create_uuid, get_current_datetime_utc


class FirestoreLock:
    TIME_TO_LIVE: float = 60.0

    def __init__(
        self,
        client: firestore.AsyncClient,
        lock_collection: str,
        lock_owner: str,
        top_level_collection: str = "",
        top_level_document: str = "",
    ):
        """Custom class designed to manage process synchronization, using Firestore
        documents as locks. This class should be used to coordinate operations
        in parallelized applications (i.e., allow a parallel-sequential-parallel flow),
        where tasks need to switch between parallel and sequential execution to avoid
        race conditions. The class can be used as a context manager (recommended),
        or by manually calling the `acquire()` and `release()` methods. Examples:

        ```
        f = FirestoreLock(
            client=client,
            lock_collection="foo",
            top_level_document="bar",
            top_level_collection="baz",
            lock_owner="me",
        )
        await f.acquire()
        print("LOCK ACQUIRED, DOING STUFF")
        time.sleep(10)
        await f.release()

        async with FirestoreLock(
            client=client,
            lock_collection="foo",
            top_level_document="bar",
            top_level_collection="baz",
            lock_owner="me",
        ) as f:
            print("LOCK ACQUIRED, DOING STUFF")
            time.sleep(10)        
        ```
        """
        if (
            (top_level_collection or top_level_document)
            and not (top_level_collection and top_level_document)
        ):
            raise ValueError(
                "Pass both top_level_collection and top_level_document, or neither"
            )

        self.client = client
        self.lock_collection_ref = self._set_lock_collection_ref(
            client=client,
            lock_collection=lock_collection,
            top_level_collection=top_level_collection,
            top_level_document=top_level_document,
        )
        self.lock_owner = lock_owner

    @property
    def firestore_lock_id(self) -> UUID:
        return UUID(self.lock_document_id)

    @property
    def lock_document_id(self) -> str:
        collection_path: List[str] = list(self.lock_collection_ref._path)
        document_id: str = create_uuid(collection_path[-1])
        return document_id

    @property
    def lock_document_ref(self) -> firestore.AsyncDocumentReference:
        return self.lock_collection_ref.document(self.lock_document_id)

    async def acquire(self, max_attempts: int = 40, timeout: float = 5.0) -> str:
        attempts = 0
        firestore_lock = schemas.FirestoreLock(
            id=self.firestore_lock_id, lock_owner=self.lock_owner,
        )

        while attempts < max_attempts:
            lock_doc = await self.lock_document_ref.get()
            if not lock_doc.exists:
                try:
                    _ = await self.lock_document_ref.create(json.loads(firestore_lock.model_dump_json()))
                    logging.debug(
                        f"Firestore lock acquired at attempt {attempts}, lock owner: {self.lock_owner}"
                    )
                    return self.lock_document_id
                except AlreadyExists:
                    logging.warning(
                        f"Attempt {attempts} by {self.lock_owner} to acquire Firestore lock failed; "
                        "competing process acquired lock first, sleeping..."
                    )

            else:   # another process has claimed the lock, check if lock is still valid
                lock_doc_parsed = schemas.FirestoreLock(**lock_doc.to_dict())   # type: ignore
                now = get_current_datetime_utc()
                if lock_doc_parsed.lock_created + timedelta(seconds=FirestoreLock.TIME_TO_LIVE) < now:  # lock has expired
                    _ = await self.lock_document_ref.set(json.loads(firestore_lock.model_dump_json()))
                    logging.info(
                        f"Firestore lock acquired at attempt {attempts} by overriding existing lock, "
                        f"new lock owner: {self.lock_owner}"
                    )
                    return self.lock_document_id
                else:
                    logging.warning(
                        f"Attempt {attempts} by {self.lock_owner} to acquire Firestore lock failed; "
                        "lock still valid, sleeping..."
                    )

            await asyncio.sleep(timeout)
            attempts += 1
            firestore_lock.lock_created_after_attempt += 1
            firestore_lock.lock_created = get_current_datetime_utc()

        raise TimeoutError(
            f"Unable to acquire Firestore lock after {max_attempts} attempts by {self.lock_owner}"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_random(), reraise=True)
    async def release(self) -> str:
        _ = await self.lock_document_ref.delete()
        logging.debug(f"Firestore lock released by {self.lock_owner}")
        return self.lock_document_id

    async def __aenter__(self):
        _ = await self.acquire()
        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self.release()

    def _set_lock_collection_ref(
        self,
        client: firestore.AsyncClient,
        lock_collection: str,
        top_level_collection: str,
        top_level_document: str,
    ) -> firestore.AsyncCollectionReference:
        if top_level_collection and top_level_document:
            return client.collection(
                top_level_collection
            ).document(
                top_level_document
            ).collection(
                lock_collection
            )
        else:
            return client.collection(lock_collection)
