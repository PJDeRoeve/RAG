import base64
import json
from typing import AsyncGenerator, Any

import fastapi
from aiohttp import ClientSession, ClientTimeout
from google.cloud import firestore
from google.oauth2.service_account import Credentials
from embed.cohere import Cohere
from embed.cohere.schema import EmbeddingModel
import en_core_web_sm
from rag.settings import settings


async def get_client_session() -> AsyncGenerator[ClientSession, Any]:
    session = ClientSession(timeout=ClientTimeout(total=3600))
    try:
        yield session
    finally:
        await session.close()


def get_cohere_handler(session: ClientSession = fastapi.Depends(get_client_session)) -> Cohere:
    return Cohere(session=session, key=settings.COHERE_API_KEY, model=EmbeddingModel.embed_multilingual_v3)

def get_ner_model():
    return en_core_web_sm.load()



def get_firestore_client() -> firestore.AsyncClient:
    service_acc_info: dict = json.loads(
        base64.b64decode(settings.GCP_SERVICE_ACCOUNT).decode()
    )
    credentials = Credentials.from_service_account_info(service_acc_info)
    client = firestore.AsyncClient(credentials=credentials)
    return client
