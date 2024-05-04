# _*_ coding:utf-8 _*_

import hashlib
import os
import subprocess
import requests
import re
import json
import time
from pprint import pprint



#
#   @作用    ：获取当前时间对应的字符串。
#   @参数    ：无。
#   @返回值  ：当前时间对应的字符串。
def get_time_date() -> str:

    date = time.strftime('%Y-%m-%d_%H:%M:%S')
    return date



#
#   @作用    ：根据cookie和视频id下载视频到./video/下。
#   @参数    ：Cookie      用户的Cookie，添加可以下载1080p画质，如果没有Cookie只能下载最低画质。
#              video_id     视频BV号。
#   @返回值  ：无。
def download_video(Cookie: str, video_id: str):
    
    # 视频网页url
    bilibili_url = 'https://www.bilibili.com/video/'
    url = bilibili_url + video_id + '/' 

    # 请求头
    header = {
        'Referer': 'https://www.bilibili.com/video/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
    }   

    # 如果有Cookie就添加到请求头
    if not Cookie.isspace():
        header.update({'Cookie': Cookie})   

    # 获取视频网页信息
    data_text = requests.get(url=url, headers=header).text  

    # 获取视频标题
    video_title = re.search(r'<script>window.__INITIAL_STATE__=(.*?);\(function\(\)', data_text).group(1)
    video_title = json.loads(video_title)
    video_title =video_title['videoData']['title'].replace(' ', '')

    # 去除文件命名不合规字符
    error_char = r'[\/\\\:\*\?\"\<\>\|]'
    video_title = re.sub(error_char, '_', video_title)  

    # 提取播放信息
    json_text = re.search(r'<script>window.__playinfo__=(.*?)</script>', data_text).group(1)
    json_data = json.loads(json_text)   

    # 提取具体的音视频url
    audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
    video_url = json_data['data']['dash']['video'][0]['baseUrl']    

    # 获取音视频的二进制内容
    audio_data = requests.get(url=audio_url, headers=header).content
    video_data = requests.get(url=video_url, headers=header).content    

    # 判断当前目录用于存储文件夹是否存在
    if not os.path.exists('./video'):
        os.mkdir('./video') 

    # 如果视频名字为空，则使用当前时间命名
    if video_title.isspace():
        video_title = get_time_date()   

    # 设置路径和文件名
    audio_path = './video/test_audio.mp3'
    video_path = './video/test_video.mp4'
    output_path = f'./video/{video_title}.mp4'
    print(f'{audio_path}\n{video_path}\n{output_path}') 

    # 音视频分别写入临时文件
    with open(audio_path, 'wb') as ofile:
        ofile.write(audio_data)
    with open(video_path, 'wb') as ofile:
        ofile.write(video_data) 

    # 命令行调用ffmpeg对音视频合成
    cmd = f'ffmpeg -i {audio_path} -i {video_path} -c:v copy {output_path}'
    subprocess.run(cmd) 
    
    # 删除临时文件
    os.remove(audio_path)
    os.remove(video_path)





#
#   @作用   ：此函数用于获取b站热门视频榜单前100的视频信息。
#   @参数   ：无。
#   @返回值 ：字典。key包含视频标题，value包含视频信息。
def get_video_list() -> dict:

    #
    #   查看网页内容得以下：
    #   视频列表json文件的url = https://api.bilibili.com/x/web-interface/popular?ps=20&pn=1&web_location=333.934&w_rid=217bf270ade9f727e51f628b27548ba2&wts=1712979415
    #     url = ... + ps + pn + web_location + w_rid                                //ps为视频数，pn为页数。
    #   w_rid = md5(m + o)      // MD5加密
    #       m = 2837%2C2836%2C2870%2C2953%2C2954%2C2955%2C2956%2C5672&pf=0&wts      // 时间戳与特定数据的组合
    #       o = ea1db124af3c7062474693fa704f4ff8

    # 函数返回的字典
    item_dict = {}

    # 获取时间戳，组合成url元素
    wts = int(time.time())
    u = ['2837%2C2836%2C2870%2C2953%2C2954%2C2955%2C2956%2C5672', 'pf=0', f'wts={wts}']
    m = '&'.join(u)     # 以'&'组合
    o = 'ea1db124af3c7062474693fa704f4ff8'

    # MD5加密，获取十六进制字符串摘要
    w_rid = hashlib.md5((m+o).encode(encoding='UTF-8')).hexdigest()

    # 请求头
    header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'
    }

    # 一共5页，一页20个视频
    for pn in range(1, 6):

        # 具体url                                                         页数                          MD5加密内容    时间戳
        url = f'https://api.bilibili.com/x/web-interface/popular?ps=20&pn={pn}&web_location=333.934&w_rid={w_rid}&wts={wts}'

        # 解析json成python对象
        json_data = requests.get(url=url, headers=header).json()

        # 获取视频字典列表
        video_list = json_data['data']['list']

        # 此页20个视频，提取信息保存至将返回的信息字典中
        for video in video_list:
            info = {
                '标题':video['title'],
                'bvID':video['bvid'],
                '作者mid':video['owner']['mid'],
                '作者名字':video['owner']['name'],
                '观看':video['stat']['view'],
                '转发':video['stat']['share'],
                '投币':video['stat']['coin'],
                '点赞':video['stat']['like'],
                '收藏':video['stat']['favorite'],
                '评论':video['stat']['reply']
            }
            # { 标题:信息 }
            item_dict.update({info['标题']:info})

    return item_dict