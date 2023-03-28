import asyncio
import base64
import hashlib
from pathlib import Path

from aiohttp import ClientSession

from asyncio_download.utils import chunked

API_URL = 'https://gitea.{}.group/api/v1/repos/{}/{}/git/trees/{}?recursive=true'


async def get_files_list(session: ClientSession, url: str) -> list[dict]:
    async with session.get(url) as response:
        return (await response.json())['tree']


async def download_file_and_get_hash(session: ClientSession, path: str | Path, url: str):
    async with session.get(url) as response:
        answer = await response.json()
        file_hash = hashlib.sha256()
        content = base64.b64decode(answer['content'])
        file_hash.update(content)
        print(f'HASH {path}: {file_hash.hexdigest()}')
        with open(path, 'wb') as file:
            file.write(content)
        return file_hash.hexdigest()


async def chunked_download(
    session: ClientSession, lst: list[dict], chunk_size: int, folder_name: Path | str = 'downloadfiles'
):
    for chunked_files in chunked(lst, chunk_size):
        tasks = []
        for file in chunked_files:
            path = folder_name / Path(file['path'])
            if file['type'] == 'blob':
                tasks.append(download_file_and_get_hash(session, path, file['url']))
            elif file['type'] == 'tree':
                path.mkdir()
        await asyncio.gather(*tasks)


async def download_files_from_gitea(
    domain: str, company: str, project_name: str, branch: str, folder_name: Path | str = 'downloadfiles'
):
    path = Path(folder_name)
    if not path.exists():
        path.mkdir()
    async with ClientSession() as session:
        url = API_URL.format(domain, company, project_name, branch)
        files_list = await get_files_list(session, url)
        await chunked_download(session, files_list, 3, folder_name)


async def main():
    domain = 'radium'
    company = 'radium'
    project_name = 'project-configuration'
    branch = 'HEAD'
    await download_files_from_gitea(domain, company, project_name, branch)


if __name__ == "__main__":
    asyncio.run(main())
