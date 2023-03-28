import shutil
from pathlib import Path

import pytest
from aiohttp import ClientSession

from asyncio_download.app import get_files_list, download_file_and_get_hash, chunked_download, download_files_from_gitea
from asyncio_download.utils import chunked

API_URL = 'https://gitea.radium.group/api/v1/repos/radium/project-configuration/git/trees/HEAD?recursive=true'
download_path = Path('test_download')


@pytest.fixture(scope='module', autouse=True)
def temp_folder():
    download_path.mkdir(exist_ok=True)
    yield
    shutil.rmtree(download_path)


@pytest.fixture
def create_session(event_loop):
    session = None

    async def maker(*args, **kwargs):
        nonlocal session
        session = ClientSession(*args, **kwargs)
        return session

    yield maker
    if session is not None:
        event_loop.run_until_complete(session.close())


@pytest.fixture
def client_session(create_session, event_loop):
    return event_loop.run_until_complete(create_session())


def test_chunk():
    lst = [0, 1, 2, 3]
    chunk_size = 2
    chunked_list = chunked(lst, chunk_size)
    assert len(chunked_list) == chunk_size
    assert chunked_list == [[0, 1], [2, 3]]


@pytest.mark.asyncio
async def test_files_list(client_session):
    lst = await get_files_list(client_session, API_URL)
    assert len(lst) > 0


@pytest.mark.asyncio
async def test_download_file_and_get_hash(client_session):
    download_url = 'https://gitea.radium.group/api/v1/repos/radium' \
                   '/project-configuration/git/blobs/d4f9f743e5073256d91cd7c160a067ab377276ee'
    path = download_path / 'README.md'
    hash = await download_file_and_get_hash(client_session, path, download_url)
    assert path.exists()
    assert hash == '8cf77a685a9b2b729f3b3ff4941e5efdbd07888ccfa96923fd1036dffe25314f'


@pytest.mark.asyncio
async def test_download_chunked(client_session):
    obj = [
        {"path": "LICENSE", "type": "blob",
         "url": "https://gitea.radium.group/api/v1/repos/radium/project-configuration"
                "/git/blobs/b9c199c98f9bec183a195a9c0afc0a2e4fcc7654"},
        {"path": "README.md", "type": "blob",
         "url": "https://gitea.radium.group/api/v1/repos/radium/project-configuration/"
                "git/blobs/d4f9f743e5073256d91cd7c160a067ab377276ee"},
        {"path": "nitpick", "type": "tree",
         "url": "https://gitea.radium.group/api/v1/repos/radium/project-configuration/"
                "git/trees/debb88cd16cfefdfe454bd8aab33ba3bce5e0977"},
        {"path": "nitpick/all.toml", "type": "blob",
         "url": "https://gitea.radium.group/api/v1/repos/radium/project-configuration/"
                "git/blobs/d862d0a9e4cf120c5a38b88d488770dbf0bf6289"}
    ]
    chunk_size = 3
    await chunked_download(client_session, obj, chunk_size, download_path)
    assert (download_path/'LICENSE').exists()
    assert (download_path / 'README.md').exists()
    assert (download_path / 'nitpick').exists()
    assert (download_path / 'nitpick' / 'all.toml').exists()


@pytest.mark.asyncio
async def test_download_from_gitea(client_session):
    domain = 'radium'
    company = 'radium'
    project_name = 'project-configuration'
    branch = 'HEAD'
    path = download_path / 'gitea'
    await download_files_from_gitea(domain, company, project_name, branch, path)
    assert (path / 'LICENSE').exists()
    assert (path / 'README.md').exists()
    assert (path / 'nitpick').exists()
    assert (path / 'nitpick' / 'all.toml').exists()
    assert (path / 'nitpick' / 'darglint.toml').exists()
    assert (path / 'nitpick' / 'editorconfig.toml').exists()
    assert (path / 'nitpick' / 'file-structure.toml').exists()
    assert (path / 'nitpick' / 'flake8.toml').exists()
    assert (path / 'nitpick' / 'isort.toml').exists()
    assert (path / 'nitpick' / 'pytest.toml').exists()
    assert (path / 'nitpick' / 'styleguide.toml').exists()
