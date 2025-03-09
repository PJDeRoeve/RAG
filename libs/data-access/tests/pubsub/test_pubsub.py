import pytest
from tests.conftest import ArtistDAO, Artist


@pytest.mark.asyncio
async def test_create_topic(artist_dao: ArtistDAO):
    topic_create = await artist_dao.create_topic()
    assert topic_create == "projects/story-chief-161712/topics/artist"
    topic_delete = await artist_dao.delete_topic()
    assert topic_delete == "projects/story-chief-161712/topics/artist"


@pytest.mark.asyncio
async def test_create_pull_subscription(artist_dao: ArtistDAO):
    _ = await artist_dao.create_topic()
    subscription_create = await artist_dao.create_pull_subscription()
    assert subscription_create == "projects/story-chief-161712/subscriptions/music-lover-dude"
    subscription_delete = await artist_dao.delete_subscription()
    assert subscription_delete == "projects/story-chief-161712/subscriptions/music-lover-dude"
    _ = await artist_dao.delete_topic()


@pytest.mark.asyncio
async def test_publish_pull_messages(artist_dao: ArtistDAO):
    artists = [
        Artist(
            name="Claude Debussy",
            genre="Impressionist",
            most_famous_work="Clair de Lune",
        ),
        Artist(
            name="Igor Stravinsky",
            genre="20th Century",
            most_famous_work="The Rite of Spring",
        ),
        Artist(
            name="Antonio Vivaldi", genre="Baroque", most_famous_work="The Four Seasons"
        ),
        Artist(name="Franz Schubert", genre="Romantic", most_famous_work="Ave Maria"),
        Artist(
            name="Pyotr Ilyich Tchaikovsky",
            genre="Romantic",
            most_famous_work="The Nutcracker",
        ),
    ]
    _ = await artist_dao.create_topic()
    _ = await artist_dao.create_pull_subscription()
    message_ids = await artist_dao.publish(artists)
    assert len(message_ids) == 5
    messages = await artist_dao.pull_messages(num_messages=30)
    assert all(message.__class__ == Artist for message in messages)
    assert len(messages) == 5
    _ = await artist_dao.delete_subscription()
    _ = await artist_dao.delete_topic()


@pytest.mark.asyncio
async def test_whether_message_is_gone_after_acknowledging(artist_dao: ArtistDAO):
    artist_dao.topic = "temp_artist"
    artist_dao.subscription = "temp_artist_subscription"
    
    # Create a new topic and subscription
    _ = await artist_dao.create_topic()
    _ = await artist_dao.create_pull_subscription()
    
    # Publish some messages
    temp_artist_list = [
        Artist(name="Glass Animals", genre="Indie", most_famous_work="Heat Waves"),
        Artist(name="The Beatles", genre="Rock", most_famous_work="Hey Jude"),
        Artist(name="The Rolling Stones", genre="Rock", most_famous_work="Paint It Black"),
    ]
    _ = await artist_dao.publish(temp_artist_list)

    # Pull the messages and verify that the messages were fetched
    messages = await artist_dao.pull_messages(num_messages=3)
    assert len(messages) == 3
    
    # Pull again and verify that the messages are gone
    messages = await artist_dao.pull_messages(num_messages=3)
    assert len(messages) == 0

    # Clean up
    _ = await artist_dao.delete_topic()
    _ = await artist_dao.delete_subscription()
