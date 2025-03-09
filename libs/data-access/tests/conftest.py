import json
from typing import AsyncGenerator

import pytest
from aiohttp import ClientSession, ClientTimeout
from google.cloud import firestore
from google.oauth2.service_account import Credentials

from data_access.pubsub.async_.dao import PubSubDAO
from data_access.pubsub.async_.dependencies import get_pubsub_publisher_client, get_pubsub_subscriber_client
from data_access.pubsub.schema import PubsubObject
from data_access.settings import settings


@pytest.fixture()
def get_firestore_async_client() -> firestore.AsyncClient:
    service_acc_info: dict = json.loads(settings.GCP_SERVICE_ACCOUNT)
    credentials = Credentials.from_service_account_info(service_acc_info)
    client = firestore.AsyncClient(credentials=credentials)

    return client


class Artist(PubsubObject):
    name: str
    genre: str
    most_famous_work: str | None = None


class ArtistDAO(PubSubDAO[Artist]):
    topic = "artist-topic-test-6"
    subscription = "music-lover-dude-test-6"


@pytest.fixture()
@pytest.mark.asyncio
async def artist_dao() -> AsyncGenerator[ArtistDAO, None]:
    session = ClientSession(timeout=ClientTimeout(total=600))
    try:
        yield ArtistDAO(
            schema_definition=Artist,
            session=session,
            project_id=settings.GCP_PROJECT_ID,
            publisher_client=get_pubsub_publisher_client(
                service_acc_b64_encoded=settings.PUBSUB_SERVICE_ACC,
                session=session,
            ),
            subscriber_client=get_pubsub_subscriber_client(
                service_acc_b64_encoded=settings.PUBSUB_SERVICE_ACC,
                session=session,
            ),
        )
    finally:
        await session.close()
