"""Contains the general synchronous Firestore DAO. Can be used as a base for other DAOs, 
but should not be used directly."""

import abc
import json
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Generic, List, TypeVar

from google.api_core.retry import Retry
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import BaseQuery
from tenacity import stop_after_attempt, wait_random, retry, retry_if_not_exception_type

from data_access.errors import DAOError, DAONotFoundError
from data_access.firestore.synchronous.schemas import (
    FirestoreFilter,
    FirestoreObject,
    FirestoreObjectCreate,
    FirestoreOrder,
)

FirestoreCreateSchemaType = TypeVar(
    "FirestoreCreateSchemaType", bound=FirestoreObjectCreate
)
FirestoreGetSchemaType = TypeVar("FirestoreGetSchemaType", bound=FirestoreObject)


class FirestoreDAO(abc.ABC, Generic[FirestoreGetSchemaType, FirestoreCreateSchemaType]):
    """The base FirestoreDAO. Should be used as a base class for real DAOs.

    Contains the following class variables:
    - collection_name: The name of the collection in firestore.
    - top_level_collection: Namespaced collection in firestore.
    - top_level_document: Namespaced document in the top_level_document.
    """

    collection_name: str = ""
    top_level_collection: uuid.UUID | str | None = None
    top_level_document: uuid.UUID | None = None

    def __init__(
        self,
        schema_definition: type[FirestoreGetSchemaType],
        client: firestore.Client,
    ):
        """Create a FirestoreDAO.

        Args:
            schema_definition: The class that will be used to parse objects
                coming from firestore.
            client: Firestore client (sync).
        """
        self.schema_definition = schema_definition
        self.client = client

    @property
    def collection(self) -> firestore.CollectionReference:
        """Set the collection property. If nested fields are defined, traverse the tree."""
        collection: firestore.Client = self.client
        if self.top_level_collection and self.top_level_document:
            collection: firestore.DocumentReference = self.client.collection(
                str(self.top_level_collection)
            ).document(str(self.top_level_document))

        return collection.collection(self.collection_name)

    @property
    def parent_collection(self) -> firestore.CollectionReference:
        """Set the collection property. If nested fields are defined, traverse the tree."""
        collection: firestore.Client = self.client
        return collection.collection(str(self.top_level_collection))

    def set_top_level_document(self, top_level_document: uuid.UUID):
        if not isinstance(top_level_document, uuid.UUID):
            raise DAOError(
                message="'top_level_document' should be a UUID"
            )
        elif self.top_level_collection is None:
            raise DAOError(
                message="Top level document can only be set on DAOs with a top level collection"
            )
        self.top_level_document = top_level_document

    def reset_top_level_document(cls):
        cls.top_level_document = None

    def set_top_level_collection(self, top_level_collection: str | uuid.UUID):
        if not isinstance(top_level_collection, (str, uuid.UUID)):
            raise DAOError(
                message="'top_level_collection' should be a str or UUID object"
            )
        self.top_level_collection = top_level_collection

    def set_collection_name(self, collection_name: str | uuid.UUID):
        if not isinstance(collection_name, (str, uuid.UUID)):
            raise DAOError(
                message="'collection_name' should be a str or UUID object"
            )
        self.collection_name = collection_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random(1, 2),
        retry=retry_if_not_exception_type(DAOError),
        reraise=True,
    )
    def create(
        self, obj_create: FirestoreCreateSchemaType, return_obj: bool = True
    ) -> FirestoreGetSchemaType | None:
        """Create an object and return the created object.

        Args:
            obj_create: FirestoreCreateSchemaType: Object to create.
            return_obj: bool: Whether or not the created object should be returned.
        Returns:
            Created object if `return_obj` is True, otherwise None.
        Raises:
            DAOError: If `return_obj` is True and the object cannot be retrieved after creation.
        """
        try:
            data: dict = json.loads(obj_create.model_dump_json())
            doc_ref: firestore.DocumentReference = self.collection.document(
                str(obj_create.id)
            )
            doc_ref.set(data)
            if return_obj is True:
                return self.get(obj_create.id)
        except DAONotFoundError as e:
            raise DAOError(
                message=f"Object {str(obj_create.id)} could not be created in {self.collection_name}",
            ) from e

    @retry(stop=stop_after_attempt(3), wait=wait_random(0.1, 0.8), reraise=True)
    def get(self, obj_id: uuid.UUID) -> FirestoreGetSchemaType:
        """Get an object by UUID.

        Args:
            obj_id: the object UUID in firestore.

        Returns:
            The object, if it exists.

        Raises:
            DAONotFoundError: When the object could not be found.
        """
        doc_ref: firestore.DocumentReference = self.collection.document(str(obj_id))
        doc: firestore.DocumentSnapshot = doc_ref.get()
        if doc.exists is True:
            return self.schema_definition(**doc.to_dict())
        raise DAONotFoundError(f"Item {str(obj_id)} not found in {self.collection_name}")

    @retry(stop=stop_after_attempt(3), wait=wait_random(1, 2), reraise=True)
    def exists(self, obj_id: uuid.UUID | None) -> bool:
        """Check if an object exists by UUID.

        Args:
            obj_id: the object UUID in firestore.

        Returns:
            True if the object exists, otherwise False.
        """
        doc_ref: firestore.DocumentReference = self.collection.document(str(obj_id))
        doc: firestore.DocumentSnapshot = doc_ref.get()
        return doc.exists

    @retry(stop=stop_after_attempt(3), wait=wait_random(1, 2), reraise=True)
    def parent_exists(self, obj_id: uuid.UUID) -> bool:
        """Check if the top_level_collection and a certain obj_id exist.

        Args:
            obj_id: the object UUID in firestore.

        Returns:
            True if the object exists, otherwise False.
        """
        parent_object: firestore.DocumentSnapshot = self.parent_collection.document(
            str(obj_id)
        ).get()
        return parent_object.exists

    @retry(stop=stop_after_attempt(3), wait=wait_random(1, 2), reraise=True)
    def set(self, obj_id: uuid.UUID, obj_set: FirestoreCreateSchemaType) -> None:
        """Add properties to an already existing object.

        Args:
            obj_id: the object UUID in firestore.
            obj_set: object to update
        """
        data: dict = json.loads(obj_set.model_dump_json())
        doc_ref: firestore.DocumentReference = self.collection.document(str(obj_id))
        doc_ref.set(data, merge=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random(1, 2),
        retry=retry_if_not_exception_type(DAONotFoundError),
        reraise=True,
    )
    def delete(
        self, obj_id: uuid.UUID, cascade: bool = False, silent: bool = False
    ) -> None:
        """Delete an object based on its obj_id.

        Args:
            obj_id: the object UUID in firestore.
            cascade: bool: If True, then recursively delete all the document's subcollections too.
            silent: bool: If True, then do not throw an error in case the object does not exist.

        Raises:
            DAOError: When the object could not be deleted.
            DAONotFoundError: When the object could not be found in the database. Only applicable
                when silent is False.
        """
        doc_ref: firestore.DocumentReference = self.collection.document(str(obj_id))
        if not (silent or self.exists(obj_id=obj_id)):
            raise DAONotFoundError(f"Item {str(obj_id)} not found in {self.collection_name}")
        if cascade is True:
            with ThreadPoolExecutor(max_workers=10) as executor:
                for c in doc_ref.collections():
                    executor.submit(self._delete_collection, c)
        doc_ref.delete()
        if self.exists(obj_id=obj_id) is True:
            raise DAOError(
                message=f"Object {str(obj_id)} could not be deleted from {self.collection_name}",
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random(1, 2),
        retry=retry_if_not_exception_type(DAONotFoundError),
        reraise=True,
    )
    def delete_all(self):
        """Deletes all objects from a collection.

        Raises:
            DAOError: when a collection object could not be deleted"""
        docs = self.list()
        for doc in docs:
            self.delete(doc.id)
        num_objects_remaining: int = self.count()
        if num_objects_remaining > 0:
            raise DAOError(
                message=f"{num_objects_remaining} objects could not be deleted from {self.collection_name}",
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random(1, 2),
        retry=retry_if_not_exception_type(DAONotFoundError),
        reraise=True,
    )
    def update(self, obj_update: FirestoreGetSchemaType) -> FirestoreGetSchemaType:
        """Update an object with an existing object.

        Args:
            obj_update: The new updated object

        Returns:
            The object if update was successful, otherwise None.

        Raises:
            DAOError: if the object cannot be updated.
        """
        if self.exists(obj_id=obj_update.id) is False:
            raise DAONotFoundError(
                id=obj_update.id,
                collection=self.collection_name,
            )
        doc_ref: firestore.DocumentReference = self.collection.document(
            str(obj_update.id)
        )
        data: dict = json.loads(obj_update.model_dump_json())
        doc_ref.update(data)
        if (obj := self.get(obj_update.id)) and obj == obj_update:
            return obj
        raise DAOError(
            message=f"Object {str(obj_update.id)} could not be updated in {self.collection_name}",
        )

    @retry(stop=stop_after_attempt(3), wait=wait_random(1, 2), reraise=True)
    def list(
        self,
        page: int | None = None,
        size: int | None = None,
        filters: list[FirestoreFilter] | None = None,
        order_by: FirestoreOrder | None = None,
    ) -> Iterator[FirestoreGetSchemaType]:
        """List all objects.

        If page and size are given, use pagination.

        Args:
            page: 0-indexed page number.
            size: amount of tags per page.
            filters: optional list of where clauses to apply to the query.
            order_by: optional ordering directive.

        Yields:
            Objects in the page.
        """
        if filters is None:
            filters = []
        query = self.collection
        if page is not None and size is not None:
            query: BaseQuery = self.collection.offset(page * size).limit(size)
        for filter in filters:
            query: BaseQuery = query.where(
                filter.field_path,
                filter.op_string,
                filter.value
            )
        if order_by:
            query: BaseQuery = query.order_by(
                order_by.field_path, direction=order_by.direction
            )
        for doc in query.stream(timeout=10000,retry=Retry(timeout=60)):
            if doc.exists:
                yield self.schema_definition(**doc.to_dict())

    @retry(stop=stop_after_attempt(3), wait=wait_random(1, 2), reraise=True)
    def count(self) -> int:
        """Count the number of objects.

        This function has to fetch all objects to count them, so use this sparingly.

        Returns:
            Total amount of objects.
        """
        aggregated_result_it = self.collection.count().stream(retry=Retry(timeout=3))
        aggregated_result = [a for a in aggregated_result_it][0][0]
        count = aggregated_result.value
        return count


    @retry(stop=stop_after_attempt(3), wait=wait_random(1, 2), reraise=True)
    def average(self, field: str) -> float:
        """Calculate the average of a field in the collection.

        Args:
            field: The field to calculate the average for.

        Returns:
            The average of the field.
        """
        aggregated_result_it = self.collection.avg(field_ref=field).stream(retry=Retry(timeout=3))
        aggregated_result = [a for a in aggregated_result_it][0][0]
        average = aggregated_result.value
        return average



    def _delete_collection(
        self,
        collection_reference: firestore.CollectionReference,
        batch_size: int = 300,
    ) -> None:
        query: BaseQuery = collection_reference.limit(count=batch_size)
        while True:
            docs: List[firestore.DocumentSnapshot] = [d for d in query.stream()]
            if len(docs) == 0:
                break
            for d in docs:
                subcollections = d.reference.collections()
                d.reference.delete()
                for s in subcollections:
                    self._delete_collection(s)
            last_doc = docs[-1]
            query = collection_reference.start_after(last_doc).limit(batch_size)
