from pypi_json import PyPIJSON
from pprint import pprint
from urllib.request import urlretrieve
import tarfile
import os
from pathlib import Path


def tar_members_stripped(tar, levels_stripped=1):
    members = []
    for member in tar.getmembers():
        p = Path(member.path)
        member.path = p.relative_to(*p.parts[:levels_stripped])
        members.append(member)
    return members


def download_and_extract(package_name):

    filename = None
    url = None

    with PyPIJSON() as client:
        requests_metadata = client.get_metadata(package_name)
        pkg = requests_metadata.urls[0]
        pprint(pkg)
        filename = pkg['filename']
        url = pkg['url']


    package_filename = 'deploy/' + filename

    urlretrieve(url, package_filename)

    # open file
    with tarfile.open(package_filename) as f:
        print(f.getmembers())
        f.extractall(path='../deploy/lib', members=tar_members_stripped(f, 1))


try:
    os.mkdir("../deploy")
    os.mkdir("../deploy/lib")
except Exception as e:
    pprint(e)
    pass

download_and_extract("micropython-umqtt.simple2")
download_and_extract("micropython-umqtt.robust2")