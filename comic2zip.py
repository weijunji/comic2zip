from bs4 import BeautifulSoup
from colorama import init, Fore
from pathlib import Path
from tempfile import TemporaryDirectory
from tqdm import tqdm

import sys
import zipfile

def unzip(file, target):
    with zipfile.ZipFile(file, 'r') as zf:
        size = sum((file.file_size for file in zf.infolist()))
        with tqdm(total=size, desc='unzip file') as pbar:
            for file in zf.infolist():
                zf.extract(file, target)
                pbar.update(file.file_size)

def process(f):
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        res_path = Path(tmp_path / 'res')
        res_path.mkdir(exist_ok=True)

        unzip(f, tmp_path)
        
        opf_path = ''
        container = BeautifulSoup(open(tmp_path / 'META-INF' / 'container.xml', 'r'), "xml")
        opf_path = container.find('rootfile', attrs={'media-type': 'application/oebps-package+xml'})['full-path']

        with zipfile.ZipFile(f + '.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            opf = BeautifulSoup(open(tmp_path / opf_path, 'r'), "xml")
            cover_content = opf.find('meta', attrs={'name': 'cover'})['content']
            cover_path = tmp_path / opf.find('item', attrs={'id': cover_content})['href']
            zipf.write(cover_path, f'cover{cover_path.suffix}')

            img_num = 0
            for ref in tqdm(opf.find_all('itemref'), desc='parse and zip file'):
                html_path = tmp_path / opf.find('item', attrs={'id': ref['idref']})['href']
                html = BeautifulSoup(open(html_path), "html.parser")
                img_num += 1
                
                sub_num = 1
                for img in html.find_all('img'):
                    img_path = html_path / '../' / img.get('src')
                    zipf.write(img_path.resolve(), "{:0>4}_{}{}".format(img_num, sub_num, img_path.suffix))
                    sub_num += 1

init()
files = sys.argv[1:]
if len(files) == 0:
    input_ = input("Please input file name(split with space):")
    input_ = input_.split(" ")
    for file in input_:
        if file != '':
            files.append(file)

for file in files:
    print('-----------------------------------------')
    print(f'Process file "{file}" ...')
    try:
        f = open(file)
    except IOError:
        print(f'{Fore.RED}File "{file}" is not accessible.{Fore.RESET}')
    else:
        f.close()
        process(file)
