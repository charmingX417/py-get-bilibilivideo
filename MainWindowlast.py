# -*- coding: utf-8 -*-

import tkinter as tk
import tkinter.messagebox as MessageBox
import ttkbootstrap as ttk
import threading

from requests_uselast import *

# 封装窗口类
class MainWindow(ttk.Window):


    #
    #   @作用   ：初始化窗口，包括放置组件、创建并开始下载和刷新的线程。
    #   @参数   ：self
    #            title    窗口标题。
    #            size     窗口初始大小。
    #   @返回值 ：无。
    def __init__(self, title, size):

        # 设置主题风格
        super().__init__(themename='lumen')

        # 设置窗口标题、初始大小
        self.title(title)
        self.geometry(size)

        # 放置组件（按钮、输入框、标签......）
        self.__make_combo()

        # 创建下载队列
        self.__download_queue = []

        # 创建并开始下载线程
        self.__download_thread = threading.Thread(target=self.__download_thread_func, daemon=True)
        self.__download_thread.start()

        # 创建下载队列线程锁
        self.__download_queue_lock = threading.Lock()

        # 创建并开始刷新线程
        self.__reload_thread = threading.Thread(target=self.__reload_thread_func, daemon=True)
        self.__reload_thread.start()

        # 创建视频列表刷新的线程锁
        self.__reload_list_lock = threading.Lock()

        # 刷新信号
        self.__should_reload = False



    #
    #   @作用   ：下载线程专用函数，会一直在里面循环，直到程序关闭。如果下载队列不为空，就会执行下载。
    #   @参数   ：self
    #   @返回值 ：无。
    def __download_thread_func(self):

        while True:
            
            # 没必要一直查看队列，固0.5秒看一次。
            time.sleep(0.5)

            # 如果队列不为空，进行下载操作。
            if len(self.__download_queue):
                
                # 锁住下载队列资源
                self.__download_queue_lock.acquire()

                # 获取队头信息，包括cookie、视频bv号。
                cookie = self.__download_queue[0][0]
                bvid = self.__download_queue[0][1]

                # 出队。
                self.__download_queue.pop(0)

                # 释放线程锁
                self.__download_queue_lock.release()

                try:
                    # 调用下载函数
                    download_video(Cookie=cookie, video_id=bvid)

                except BaseException as error:
                    # 错误弹窗
                    print(error)
                    MessageBox.showerror(title='error', message=f'{bvid} 下载失败')

                else:
                    # 完成弹窗
                    MessageBox.showinfo(title='info', message=f'{bvid} 下载完成')



    #
    #   @作用   ：刷新线程专用函数，会一直在里面循环，直到程序关闭。如果有刷新的信号，就执行。
    #   @参数   ：self
    #   @返回值 ：无。
    def __reload_thread_func(self):


        while True:

            # 没必要一直查看信息，固0.5秒看一次。
            time.sleep(0.5)

            # 如果刷新信息为真，进行刷新操作。
            if self.__should_reload:

                try:
                    # 调用刷新函数，更新视频信息字典。
                    self.__video_list = get_video_list()

                    # 锁住视频列表。
                    self.__reload_list_lock.acquire()

                    # 删除列表当前所有item。
                    self.__list_box.delete(0, tk.END)

                    # 把100个视频信息插入列表显示。
                    for item in self.__video_list.items():
                        # 视频标题作为列表内容。
                        self.__list_box.insert(tk.END, item[0])

                except BaseException as error:
                    # 错误弹窗。
                    print(error)
                    MessageBox.showerror(title='error', message='刷新失败')

                finally:
                    # 释放锁
                    if self.__reload_list_lock.locked():
                        self.__reload_list_lock.release()

                # 更改刷新信息，表示已经刷新过了。
                self.__should_reload = False



    #
    #   @作用   ：创建和布置组件，管理整体布局。
    #   @参数   ：self
    #   @返回值 ：无。
    def __make_combo(self):
        
        # 创建布局管理器
        self.__frame_1 = ttk.Frame(self)
        self.__frame_2 = ttk.Frame(self)

        # cookie标签及输入框，生成于frame1中
        self.__label_cookie = ttk.Label(self.__frame_1, text='Cookie:')
        self.__edit_cookie = ttk.Entry(self.__frame_1, show='*')

        # 视频id号标签及输入框，生成于frame2中
        self.__label_video_id = ttk.Label(self.__frame_1, text='视频ID:')
        self.__edit_video_id = ttk.Entry(self.__frame_1)

        # 设置网格布局
        self.__edit_cookie.grid(row=0, column=1)
        self.__label_cookie.grid(row=0, column=0)
        self.__label_video_id.grid(row=1, column=0, pady=5) # pady表示与上一行的间隔
        self.__edit_video_id.grid(row=1, column=1, pady=5)

        # 设置按键，并连接点击槽函数                                                                         takefocous=false表示点击焦点不聚集于按键
        self.__button_video = ttk.Button(self.__frame_2, text='导出视频', width=7, command=self.__button_video_clicked, takefocus=False)
        self.__button_info = ttk.Button(self.__frame_2, text='导出信息', width=7, command=self.__button_info_clicked, takefocus=False)
        self.__button_reload = ttk.Button(self.__frame_2, text='刷新', width=7, command=self.__button_reload_clicked, takefocus=False)

        # 设置网格布局
        self.__button_reload.grid(row=0, column=0, padx=5) # padx表示与左边的间隔
        self.__button_video.grid(row=0, column=1, padx=5)
        self.__button_info.grid(row=0, column=2, padx=5)

        # 设置列表组件，用于显示热门视频列表
        self.__list_box = tk.Listbox(self, selectmode=tk.EXTENDED) # selectmode=EXTENDED表示可多选
        self.__list_box.bind('<ButtonRelease-1>', self.__list_box_clicked) # 绑定鼠标释放槽函数

        # 几个布局合并到主窗口大布局，默认从上到下
        self.__frame_1.pack()
        self.__frame_2.pack(pady=8)
        self.__list_box.pack(pady=8, fill='both')



    #
    #   视频列表组件鼠标释放后触发的槽函数。
    #
    #   @作用   ：根据当前选中的第一个内容，从视频信息字典中获取视频bv号，并显示于bv号输入框内。
    #   @参数   ：self
    #            event      于tkinter的事件机制保持一致(其中包含鼠标坐标、键盘信息等等)。
    #   @返回值 ：
    def __list_box_clicked(self, event=None): # event该函数并不需要。
        
        # 获取列表当前选中项。
        index = self.__list_box.curselection()

        # 没有选中行退出函数。
        if not index:
            return

        try:
            # 锁住列表，防止更新过程使内容变换。
            self.__reload_list_lock.acquire()

            # 获取当前选中项的第一个的内容，根据内容从信息字典中获取视频BV号
            bvid = self.__video_list[self.__list_box.get(index[0])]['bvID']

            # 删除视频BV输入框的内容，并插入当前列表选中的视频BV号
            self.__edit_video_id.delete(0, ttk.END)
            self.__edit_video_id.insert(0, bvid)

            # 释放锁。
            self.__reload_list_lock.release()
        except:
            # 错误提示。
            print('error')




    #
    #   视频下载按键的点击槽函数。
    #
    #   @作用   ：根据cookie、bvid输入框内容组合成列表，入队下载队列，等待下载。
    #   @参数   ：self
    #   @返回值 ：无。
    def __button_video_clicked(self):

        # 获取cookie、BV输入框的内容。
        cookie = self.__edit_cookie.get()
        video_bvid = self.__edit_video_id.get()

        # 锁住队列。
        self.__download_queue_lock.acquire()
        # 入队。
        self.__download_queue.append([cookie, video_bvid])
        # 释放锁。
        self.__download_queue_lock.release()



    #
    #   视频信息按键点击的槽函数。
    #
    #   @作用   ：根据当前选中项（一个或多个），生成信息文件和弹窗。
    #   @参数   ：self
    #   @返回值 ：无。
    def __button_info_clicked(self):

        # 获取视频列表选中项
        index = self.__list_box.curselection()

        # 如果没有选中则返回
        if not index:
            return
        
        # 检测存放视频信息的文件夹是否存在，不存在就创建
        if not os.path.exists('./info'):
            os.mkdir('./info')

        # 多选的内容一个个拿出来
        for i in index:

            # 原视频标题
            title_source = self.__list_box.get(i)

            # 文件命名不允许的字符
            error_char = r'[\/\\\:\*\?\"\<\>\|]'

            # 去除不合规字符，用于创建保存信息的文件。
            title_file = re.sub(error_char, '_', title_source).replace(' ', '')

            # 设置路径。
            file_path = f'./info/{title_file}.txt'

            # 生成文件。
            with open(file_path, mode='w', encoding='utf-8') as ofile:

                # 从信息字典中获取视频信息
                info = self.__video_list[title_source]
                output_str = f'''
                标题: {info['标题']}
                bvID: {info['bvID']}
                作者mid: {info['作者mid']}
                作者名字: {info['作者名字']}
                观看: {info['观看']}
                转发: {info['转发']}
                投币: {info['投币']}
                点赞: {info['点赞']}
                收藏: {info['收藏']}
                评论: {info['评论']}
                '''
                ofile.write(output_str)

                # 视频信息展示框
                MessageBox.showinfo(title='video_info', message=output_str)


    # 
    #   刷新列表按键点击的槽函数。
    #
    #   @作用   ：触发刷新信号。
    #   @参数   ：self
    #   @返回值 ：无。
    def __button_reload_clicked(self):

        # 如果信息为空，更改信息
        if self.__should_reload == False:
            self.__should_reload = True



    #
    #   @作用   ：显示窗口。
    #   @参数   ：self
    #   @返回值 ：无。
    def show(self):
        self.mainloop()



window = MainWindow(title='hello', size='400x300+100+100')
window.show()

