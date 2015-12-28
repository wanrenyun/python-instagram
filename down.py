# _*_ coding=utf8 _*_
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!
import sip
sip.setapi('QString', 2)
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Dialog(QtGui.QDialog):

    def __init__(self, parent=None):
        import sys
        reload(sys)
        sys.setdefaultencoding('utf-8')
        super(Dialog, self).__init__(parent)

        self.openFilesPath = ''

        self.errorMessageDialog = QtGui.QErrorMessage(self)

        frameStyle = QtGui.QFrame.Sunken | QtGui.QFrame.Panel

        self.nameLabel = QtGui.QLabel("Instagram NickName:")
        self.nameEdit = QtGui.QLineEdit()
        self.nameEdit.setObjectName(_fromUtf8("textEdit"))
        self.nameLabel.setBuddy(self.nameEdit)
        self.downButton = QtGui.QPushButton("DownLoad Now")

        self.saveFileNameLabel = QtGui.QLabel()
        self.saveFileNameLabel.setFrameStyle(frameStyle)
        self.saveFileNameButton = QtGui.QPushButton("Save Path :")

        self.showInfo = QtGui.QTextBrowser()  #self.showInfo.toPlainText()

        self.downButton.clicked.connect(self.begin_download)
        self.saveFileNameButton.clicked.connect(self.setSaveFileName)

        layout = QtGui.QGridLayout()
        layout.setColumnStretch(1, 1)
        layout.setColumnMinimumWidth(1, 250)

        layout.addWidget(self.nameLabel, 1, 0)
        layout.addWidget(self.nameEdit, 1, 1)
        layout.addWidget(self.saveFileNameButton, 2, 0)
        layout.addWidget(self.saveFileNameLabel, 2, 1)
        layout.addWidget(self.downButton, 3, 0, 1, 1)
        layout.addWidget(self.showInfo, 4, 0, 4, 2)

        self.setLayout(layout)
        self.resize(600, 500);
        self.setWindowTitle("Instagram Resources Download")

    def setSaveFileName(self):
        options = QtGui.QFileDialog.ShowDirsOnly
        fileName = QtGui.QFileDialog.getExistingDirectory(self,
                "Select Save Path",
                self.saveFileNameLabel.text(),
                options)
        if fileName:
            self.saveFileNameLabel.setText(fileName)
    def begin_download(self):
        #print(self.nameEdit.text())
        #print(self.saveFileNameLabel.text())
        get_instagram_images(self,[(self.nameEdit.text(),self.nameEdit.text())],
                         path=self.saveFileNameLabel.text(),
                         thread_num=int(20))
import requests
import urllib
import re
import threading
import time
import os
import logging
import errno
import argparse
import json

user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'

mylock = threading.RLock()
retry_list = []

web_url = "https://instagram.com/"
json_url = "https://instagram.com/{0}/media/?max_id={1}"

time_img_created_regex = r'data-utime=\"(?P<utime>\d+)\"'
#first_page_regex = '\"id\":\"(?P<img_id>\d+)_\d+?\",\"user":\{\"username\":".+?\"'
first_page_regex = r'\"(start_cursor)\":\"(?P<img_id>\d+)\"'  # "start_cursor": "1139676120822172755",

def get_instagram_images(self,target_usr_list, path='.', thread_num=20):
    self.showInfo.setText("")
    for (uid, uname) in target_usr_list:

        uname = clean_filename(uname)
        if len(uname) == 0:
            uname = clean_filename(str(uid))

        appendText(self,'=========================================================================')
        appendText(self,'Downloading %s\'s photos' % uname)
        sort_dir = os.path.join(path, 'instagram.photo', uname)
        mkdir_p(sort_dir)
        id_list = get_idlist(sort_dir)
        isFirsttime = False
        if len(id_list) == 0:
            isFirsttime = True
            pass
        else:
            id_list = [ids.strip() for ids in id_list]

        session = requests.session()
        session.headers['User-Agent'] = user_agent

        pic_list = []
        video_list = []
        #print( 'Parsing...')
        appendText(self,'Parsing...')
        url = web_url + uid
        appendText(self,'begin to down from %s......'% url)
        #logging.info('first page: %s', url)
        page = get_page(session, url, retry_times=5)
        appendText(self,'begin to down from %s......'% url)
       # print(page.encode("GB18030"))
        if page:
            first_photo_item = re.search(first_page_regex, page)
            #print(first_photo_item.group(2))
            appendText(self,first_photo_item.group(2))
            #exit()
        else:
            #print ('First page error.')
            appendText(self,'First page error.')

        #url = json_url.format(uid, '1', first_photo_item.group('img_id'))
        #url="https://www.instagram.com/oddkidout/media/?max_id=1048769333784892226"
        #url="https://www.instagram.com/wanrenyun/media/?max_id=1139676120822172756"
        url = json_url.format(uid, int(first_photo_item.group('img_id'))+1)
#       # exit()
        page = get_page(session, url, retry_times=5)

        page_num = 1
        while page is not None:
            time_begin = time.time()
            j_page = json.loads(page)
            page = None
            tmp_pic_num = 0
            tmp_video_num = 0
           # print(j_page)

            for photo_item in j_page['items']:

                # get caption of the img
               # exit()
                if photo_item['caption']:
                    caption = clean_filename(photo_item['caption']['text'])
                else:
                    caption = ''
                # get created time of the img

                utime = photo_item['created_time']
                img_time = time.strftime('%Y%m%d%H%M', time.gmtime(float(utime)))

                # get multimedia object url
                if 'videos' in photo_item:
                    video_url = photo_item['videos']['standard_resolution']['url']
                    video_id = video_url.split('/')[-1]
                    if video_id not in id_list:
                        video_list.append((img_time, caption, video_id, video_url))
                        pic_list.append((img_time, caption, video_id, video_url))
                        tmp_video_num += 1
                        logging.info('%s', caption.encode('cp936', 'ignore'))
                        logging.info('video_url: %s', video_url)
                    else:
                        break

                elif 'images' in photo_item:
                    img_url = photo_item['images']['standard_resolution']['url']
                    img_id =  img_url.split('/')[-1]
                    if img_id not in id_list:
                        pic_list.append((img_time, caption, img_id, img_url))
                        tmp_pic_num += 1
                        logging.info('%s', caption.encode('cp936', 'ignore'))
                        logging.info('img_url: %s', img_url)
                    else:
                        break

            if tmp_video_num + tmp_pic_num > 0:
                if j_page['more_available']:
                    url = json_url.format(uid, photo_item['id'])
                    page = get_page(session, url, retry_times=5)
            time_end = time.time()
            appendText(self,'Page %3d:   %2d new (photo: %d, video: %d)  Time used: %.2f secs' % (page_num,
                                                                  tmp_video_num + tmp_pic_num,
                                                                  tmp_pic_num,
                                                                  tmp_video_num,
                                                                  time_end-time_begin))

            page_num += 1

        appendText(self,' ')
        #print ('%d new items(%d videos) found since last update!' % (len(pic_list), len(video_list)))
        appendText(self,'%d new items(%d videos) found since last update!' % (len(pic_list), len(video_list)))
        # print(pic_list)
        if len(pic_list) == 0:
            continue

        # for debug
        # set_testlist('.', pic_list)

        # 传入整个list的大小，如果大于配置文件中的数值则按 THREAD 数目分片，否则按照 list 大小分片
        pic_list_div = div_list(pic_list, thread_num)
        threads = []
        times = len(pic_list_div)
        for i in range(times):
            th = (threading.Thread(target=download, args=(session, pic_list_div[i], sort_dir)))
            threads.append(th)
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        attempts_times = 1
        while len(retry_list) != 0 and attempts_times < 5:

            #print( 'Now retrying the [ %s ] failed task!!!' % len(retry_list))
            appendText(self,'Now retrying the [ %s ] failed task!!!' % len(retry_list))
            threads = []
            # 分多线程进行重试
            pic_list_div = []
            pic_list_div = div_list(retry_list, thread_num)
            for i in range(len(pic_list_div)):
                th = threading.Thread(target=retry_download, args=(session, pic_list_div[i], sort_dir))
                threads.append(th)

            for th in threads:
                th.start()
            for th in threads:
                th.join()

            attempts_times += 1

        done_list = list(set(pic_list) - set(retry_list))
        set_idlist(sort_dir, list(done_list))
        if len(retry_list)== 0:
            #print( 'All %s \'s download jobs has been done.' % uname)
            appendText(self,'All %s \'s download jobs has been done.' % uname)
        else:
            #print ('%d items failed.' % len(retry_list))
            appendText(self,'%d items failed.' % len(retry_list))
def appendText( self, text ):
    self.showInfo.append(text)
def div_list(picname_list, thread_num):
    '''
    divide the list into small lists, if sum < thread_num then divide by sum
    '''
    sum = len(picname_list)
    if sum < thread_num:
        thread_num = sum

    # round up
    size = int((len(picname_list) + thread_num - 1) / thread_num)

    l = [picname_list[i:i + size] for i in range(0, len(picname_list), size)]

    return l


def download(session, pic_list, sort_dir):
    for (img_time, caption, picname, pic_url) in pic_list:
        try:
            # max length of filename including path defined by windows is 256
            # cut the caption str if needed
            cur_dir_length = len(os.path.abspath(sort_dir))
            max_cap_length = 255 - len(img_time) - len(picname) - cur_dir_length - 3
            if len(caption) > max_cap_length:
                tmp_caption = caption[0:max_cap_length] + u'…'
            else:
                tmp_caption = caption
            filename = img_time + '.' + tmp_caption + '.' + picname
            filename = clean_filename(filename)
            fn = os.path.join(sort_dir, filename)
            logging.info("%s: Begin to retrieve %s.",threading.currentThread(), picname)
            urllib.urlretrieve(pic_url, fn)
            logging.info("%s: %s downloaded successfully.",threading.currentThread(), picname)
            print picname + ' downloaded successfully.'
        except Exception as e:
            print (e)
            mylock.acquire()
            retry_list.append((img_time, caption, picname, pic_url))
            mylock.release()
            logging.info("%s: Failed to retrieve %s.",threading.currentThread(), picname)
            print '%s downloading failed, add to retry queue!' % picname


def retry_download(session, picname_list, sort_dir):
    '''
    retry to download the failed task until all images has been dowloaded successfully.
    '''
    for (img_time, caption, picname, pic_url) in picname_list:

        try:
            # max length of filename including path defined by windows is 256
            # cut the caption str if needed
            cur_dir_length = len(os.path.abspath(sort_dir))
            max_cap_length = 255 - len(img_time) - len(picname) - cur_dir_length - 3
            if len(caption) > max_cap_length:
                tmp_caption = caption[0:max_cap_length] + u'…'
            else:
                tmp_caption = caption
            filename = img_time + '.' + tmp_caption + '.' + picname
            filename = clean_filename(filename)
            fn = os.path.join(sort_dir, filename)
            urllib.urlretrieve(pic_url, fn)

            mylock.acquire()
            try:
                retry_list.remove((img_time, caption, picname, pic_url))
            finally:
                mylock.release()

            print picname + 'downloaded successfully.'
        except Exception as e:
            print e
            print '%s downloading failed, add to retry queue!' % picname



def get_idlist(sort_dir):
    ''' get the pic_id which has already downloaded.
    '''
    filename = os.path.join(sort_dir, 'id_list.log')
    if os.path.exists(filename):
        f = open(filename, 'r')
        id_list = f.readlines()
        f.close()
    else:
        id_list = []

    return id_list

def set_testlist(sort_dir, ids):
    ''' store the pic_id into id_list.log
    '''
    filename = os.path.join(sort_dir, 'test.log')
    f = open(filename, 'w')

    slist = [('%s|%s|%s|%s\n' % (img_time, caption, picname, pic_url)).encode('utf8') for (img_time, caption, picname, pic_url) in ids]
    f.writelines(slist)
    f.close()

def get_testlist(sort_dir):
    ''' get the pic_id which has been already downloaded.
    '''
    filename = os.path.join(sort_dir, 'test.log')
    if os.path.exists(filename):
        f = open(filename, 'r')
        id_list = f.readlines()
        f.close()
    else:
        id_list = []

    return id_list

def set_idlist(sort_dir, ids):
    ''' store the pic_id into id_list.log
    '''
    filename = os.path.join(sort_dir, 'id_list.log')
    f = open(filename, 'a')
    ids = [picname + '\n' for (img_time, caption, picname, pic_url) in ids]

    f.writelines(ids)
    f.close()

def clean_filename(s, minimal_change=True):
    """
    Sanitize a string to be used as a filename.
    If minimal_change is set to true, then we only strip the bare minimum of
    characters that are problematic for filesystems (namely, ':', '/' and
    '\x00', '\n').
    """

    # strip paren portions which contain trailing time length (...)
    s = s.replace(':', '_')\
        .replace('/', '_')\
        .replace('\x00', '_')\
        .replace('\n', '')\
        .replace('\\', '')\
        .replace('*', '')\
        .replace('>', '')\
        .replace('<', '')\
        .replace('?', '')\
        .replace('\"', '')\
        .replace('|', '')

    if minimal_change:
        return s

    s = re.sub(r"\([^\(]*$", '', s)
    s = s.replace('&nbsp;', '')
    s = s.replace('?', '')
    s = s.replace('"', '\'')
    s = s.strip().replace(' ', '_')

    return s


def get_page(session, url, retry_times=3, timeout=20):
    """
    Download an HTML page using the requests session.
    """
    attempts_times = 0
    while True:
        attempts_times += 1

        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            #logging.error('Exception in get_page: %s', e)
            #logging.info('Error getting page %s, retrying... %d', url, attempts_times)
            if attempts_times >= retry_times:
                raise
            msg = 'Error getting page, retry in {0} seconds ...'
            interval = 2 ** attempts_times
            #logging.info(msg.format(interval))
            time.sleep(interval)
            continue
        break
    return r.text


def mkdir_p(path, mode=0o777):
    """
    Create subdirectory hierarchy given in the paths argument.
    """

    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    dialog = Dialog()
    sys.exit(dialog.exec_())
