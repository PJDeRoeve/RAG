import uuid
import pytest
from data_access.firestore.asynchronous.dao import FirestoreDAO
from data_access.firestore.asynchronous.schemas import FirestoreObject


class GetObjectSchema(FirestoreObject):
    id: str = "id"
    foo: str
    bar: int
    baz: dict


class CreateObjectSchema(GetObjectSchema):
    pass


class Subclass(FirestoreDAO[GetObjectSchema, CreateObjectSchema]):
    pass


@pytest.fixture(params=[Subclass], scope="function")
def yield_firestoredao_subclass(request: pytest.FixtureRequest, get_firestore_async_client):
    def yield_subclass(return_object: bool = False) -> Subclass:
        FireStoreDAOSubClass: FirestoreDAO = request.param
        if return_object is True:
            collection_name = uuid.uuid4().__str__()
            FireStoreDAOSubClass.set_collection_name(collection_name)
            subclass_object = FireStoreDAOSubClass(
                schema_definition=GetObjectSchema, client=get_firestore_async_client
            )
            return subclass_object
        else:
            return FireStoreDAOSubClass
    return yield_subclass


@pytest.mark.asyncio
@pytest.fixture(scope="function")
async def create_object_in_db(yield_firestoredao_subclass):
    subclass_obj: Subclass = yield_firestoredao_subclass(return_object=True)
    object_to_be_created = CreateObjectSchema(foo='a', bar=1, baz={'b': 2, 'c': 3})
    object_created: GetObjectSchema = await subclass_obj.create(
        obj_create=object_to_be_created
    )
    yield object_to_be_created, object_created
    await subclass_obj.delete(obj_id=object_created.id)


@pytest.mark.asyncio
@pytest.fixture(scope="function")
async def build_object_to_be_created_in_db(yield_firestoredao_subclass):
    subclass_obj: Subclass = yield_firestoredao_subclass(return_object=True)
    object_to_be_created = CreateObjectSchema(foo='d', bar=4, baz={'e': 5, 'f': 6})
    yield object_to_be_created, subclass_obj
    await subclass_obj.delete(obj_id=object_to_be_created.id)


class TestFireStoreAsync:

    def test_firestoredao_subclassing(self, yield_firestoredao_subclass):
        subclass_obj: Subclass = yield_firestoredao_subclass(return_object=True)
        assert subclass_obj.collection.id == subclass_obj.collection_name

    def test_firestore_dao_subclassing_classmethods(self, yield_firestoredao_subclass):
        collection_name: str = uuid.uuid4().__str__()
        top_level_collection: uuid.UUID = uuid.uuid4()
        top_level_document: uuid.UUID = uuid.uuid4()

        subclass: FirestoreDAO = yield_firestoredao_subclass(return_object=False)
        subclass.set_collection_name(collection_name)
        subclass.set_top_level_collection(top_level_collection)
        subclass.set_top_level_document(top_level_document)

        assert subclass.collection_name == collection_name
        assert subclass.top_level_document == top_level_document
        assert subclass.top_level_collection == top_level_collection 

    @pytest.mark.asyncio
    async def test_firestoredao_create(self, create_object_in_db):

        async for object_to_be_created, object_created in create_object_in_db:
            assert isinstance(object_to_be_created, CreateObjectSchema)
            assert isinstance(object_created, GetObjectSchema)
            assert object_to_be_created.__dict__ == object_created.__dict__

    @pytest.mark.asyncio
    async def test_firestoredao_exists(self, build_object_to_be_created_in_db):

        async for object_to_be_created, subclass_obj in build_object_to_be_created_in_db:
            assert isinstance(object_to_be_created, CreateObjectSchema)
            assert isinstance(subclass_obj, Subclass)

            object_created: GetObjectSchema = await subclass_obj.create(
                obj_create=object_to_be_created
            )
            exists = await subclass_obj.exists(object_created.id)
            assert exists is True

    @pytest.mark.asyncio
    async def test_firestoredao_update(self, build_object_to_be_created_in_db):

        async for object_to_be_created, subclass_obj in build_object_to_be_created_in_db:
            assert isinstance(object_to_be_created, CreateObjectSchema)
            assert isinstance(subclass_obj, Subclass)

            object_created: GetObjectSchema = await subclass_obj.create(
                obj_create=object_to_be_created
            )
            object_update = object_created.copy(deep=True)
            object_update.__dict__.update(**{"foo": "test", "bar": 100})
            object_updated: GetObjectSchema = await subclass_obj.update(object_update)

            assert object_created.foo != object_updated.foo
            assert object_created.bar != object_updated.bar
            assert object_created.id == object_updated.id
            assert object_created.baz == object_updated.baz
