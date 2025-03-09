import aiohttp
import pytest
from pydantic import BaseModel

from data_access.errors import CacheExpiredError
from data_access.gcstorage.asynchronous.dao import GoogleCloudStorageDAO
from data_access.gcstorage.asynchronous.dependencies import get_cloud_storage_client
from data_access.gcstorage.asynchronous.schema import GoogleCloudStorageObjectType


@pytest.mark.asyncio
async def test_get_cloud_storage_obj_valid():
    async with aiohttp.ClientSession() as session:

        class CompanyPageScrapedContentDAO(GoogleCloudStorageDAO):
            bucket_name = "stc-subtopic-pipeline"
            path = "scraped-content/"
            file_type = GoogleCloudStorageObjectType.html_text

        client = await get_cloud_storage_client(session=session)
        content_dao = CompanyPageScrapedContentDAO(client=client)
        high_cache = await content_dao.get(
            file_name="00000000-0000-4000-8000-9439d4427ccb.html", cache_period=1000
        )
    assert high_cache is not None


@pytest.mark.asyncio
@pytest.mark.xfail(raises=CacheExpiredError)
async def test_get_cloud_storage_obj_cache_expired():
    async with aiohttp.ClientSession() as session:

        class CompanyPageScrapedContentDAO(GoogleCloudStorageDAO):
            bucket_name = "stc-subtopic-pipeline"
            path = "scraped-content/"
            file_type = GoogleCloudStorageObjectType.html_text

        client = await get_cloud_storage_client(session=session)
        content_dao = CompanyPageScrapedContentDAO(client=client)
        low_cache = await content_dao.get(
            file_name="00000000-0000-4000-8000-9439d4427ccb.html", cache_period=1
        )
        assert low_cache is not None


@pytest.mark.asyncio
async def test_overwrite_obj():
    async with aiohttp.ClientSession() as session:

        class CompanyPageScrapedContentDAO(GoogleCloudStorageDAO):
            bucket_name = "stc-subtopic-pipeline"
            path = "scraped-content/"
            file_type = GoogleCloudStorageObjectType.html_text

        client = await get_cloud_storage_client(session=session)
        content_dao = CompanyPageScrapedContentDAO(client=client)

        class ScrapedContentDump(BaseModel):
            file_name: str
            file_content: str
            file_type: GoogleCloudStorageObjectType

        file_name = "00000000-0000-4000-8000-124e9531d444.html"
        obj = ScrapedContentDump(
            file_name=file_name,
            file_content="test",
            file_type=GoogleCloudStorageObjectType.html_text,
        )
        await content_dao.create(obj)
        retrieved_obj = await content_dao.get(file_name=file_name)

    assert retrieved_obj is not None
