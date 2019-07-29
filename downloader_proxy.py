import os
import urllib3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from tqdm import tqdm
from faker import Faker

urllib3.disable_warnings()


class Downloader():
    def __init__(self, url, filename=None, dst=None):
        """
        :param url: 下载地址
        :param dst: 指定下载文件输出目录 不指定则为当前目录
        :param filename: 指定下载文件名 不指定则根据url截取命名
        """
        self.url = url
        self.chunk_size = 1024 * 1000  # 设置下载文件块大小 单位为字节（多线程下载时，一个线程下载一小块）

        self.filename = filename
        self.dst = dst or os.getcwd()
        self.file_size = 0
        self.file_type = None

    def check_url(self):
        """
        判断url是否支持断点续传功能
        """
        header = {
            'User-Agent': Faker().user_agent()
        }
        res = requests.head(self.url, headers=header, verify=False)  # verify=False 关闭ssl双向验证，解决访问https报错问题

        if not (200 <= res.status_code < 400):
            print(res.status_code)
            print()
            raise Exception('Bad request!')

        headers = res.headers
        print(headers)
        self.file_size = int(headers.get('Content-Length'))
        self.file_type = headers.get('Content-Type')

        # print(self.file_size, self.file_type)
        return headers.get('Accept-Ranges') == 'bytes'

    def get_range(self):
        """
        根据设置的缓存大小以及文件大小划分字节序列
        eg: [(0, 1023), (1024, 2047), (2048, 3071) ...]
        """
        lst = range(0, self.file_size, self.chunk_size)
        _range = list(zip(lst[:-1], [i - 1 for i in lst[1:]]))
        _range.append((lst[-1], ''))
        return _range

    def download_by_piece(self, _range):
        start, stop = _range
        header = {
            "Range": f"bytes={start}-{stop}",
            'User-Agent': Faker().user_agent()
        }
        res = requests.get(self.url, headers=header, verify=False)
        if res.status_code != 206:
            raise Exception(f'Request raise error, url: {self.url}，range: {_range}')
        return _range, res.content

    def download(self):
        check_ret = self.check_url()
        if not check_ret:
            print(f'资源({self.url})不支持断点续传!')
            # TODO 直接下载

        # 文件处理
        _, filename = os.path.split(self.url)
        self.filename = self.filename or filename
        file_path = Path(self.dst) / self.filename

        if file_path.exists():
            if not check_ret:
                inp = input('指定文件已存在，是否重新下载(Y/N)?')
                if inp.lower() == 'y':
                    # TODO download
                    pass
                elif inp.lower() == 'n':
                    print('下载终止!')
                else:
                    raise Exception('指令有误，下载中断!')
                return
            else:
                # 支持断点续传, 继续下载
                # TODO 断点下载  文件完整的
                pass
        else:
            open(file_path, 'w+').close()  # 生成文件

        pool = ThreadPoolExecutor(max_workers=2)  # 默认线程数为：cpu数量 * 5
        res = [pool.submit(self.download_by_piece, r) for r in self.get_range()]

        # 初始化进度条
        pbar = tqdm(total=self.file_size, initial=0, unit='B', unit_scale=True, desc=self.filename, unit_divisor=1024)

        # 将下载的块写入文件
        with open(self.filename, 'rb+') as fp:
            for item in as_completed(res):
                _range, content = item.result()
                start, stop = _range
                fp.seek(start)
                fp.write(content)

                # 更新进度条
                pbar.update(self.chunk_size)

        pbar.close()
        print(f'\n文件({self.filename})下载完成!')


if __name__ == '__main__':
    # url = "https://pic.ibaotu.com/00/51/34/88a888piCbRB.mp4"
    # url = 'https://gss3.baidu.com/6LZ0ej3k1Qd3ote6lo7D0j9wehsv/tieba-smallvideo-transcode/31_549d3fc76642c5b7ed3d1521095f9e47_2.mp4'
    # url = 'https://emb4.xxxtube.club/x-videos/b1/e6/1498375744.00926.mp4?e=1564403050&hash=0d9ndJahqifyCro7H2V9gA'
    # https://emb4.xxxtube.club/x-videos/f2/1e/1496954858.14755.mp4?e=1564401494&hash=y1K36bZaNak0CEJeD9rUtg
    # https://emb4.teenpornlikes.com/like_free/c5/0a/1514243936.40976.mp4?e=1564403193&hash=xyiV-2jxhzyzI8kc2_ggEQ
    # https://emb4.pornopedia.pro/view/df/4c/1497015372.07184.mp4?e=1564403277&hash=dpMcR1CQNGZhGPTlT2rY8g
    # https://emb3.pornopedia.pro/view/62/19/1453762114.21163.mp4?e=1564403293&hash=q1_NRDQ7qLtoFvIW80b4zw
    # https://emb4.asianpornset.com/hd-asian/ba/75/1496328674.23608.mp4?e=1564403971&hash=yfvhb-LCRDN-mzcmD8t7dg

    url = 'https://emb4.asianpornset.com/hd-asian/ba/75/1496328674.23608.mp4?e=1564403971&hash=yfvhb-LCRDN-mzcmD8t7dg'
    # https://emb4.online-xxxmovies.com/videos/40/1e/1497120356.13946.mp4?e=1564404948&hash=pW27NBvYUbl76_Dhr1MpMA

    # https://dp1.t8cdn.com/201805/12/48870011/mp4_hd720_48870011.mp4?ri=1638400&rs=1816&ttl=1564323331&hash=87a801fec40b86aab3f8a7e3f34c8191
    # https://ep3.t8cdn.com/videos/201906/28/232109752/720P_1500K_232109752.mp4?validfrom=1564316200&validto=1564323400&rate=152k&burst=1400k&ip=27.37.146.137&hash=24Jm7zL%2FKs0rJfV7TTWgYE0FA4I%3D
    # https://emb4.asianpornset.com/hd-asian/c6/c0/1496904560.12832.mp4?e=1564406904&hash=-dm9m98dNH7Q1cmTL1m3QA
    # TODO 代理
    # https://xh.video/xembed.php?video=8845602
    # https://asianpornset.com/zh-cn/clip/cTAtMTEzNy0xNDIyMzQyNA==/Black-Pantyhose-Sales-teenager-having-Excited-Outdoor-xxx-clip/?open
    d = Downloader(url, filename='9014aa10pxr0847.mp4')
    # print(d.check_url())
    d.download()
    # TODO 代理 重试
    # TODO du -h
    # 从视频中截图图片