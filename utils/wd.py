import time
from typing import List

from selenium import webdriver
import urllib.parse
import re
import os
import schema

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FormattedUrl:
    def __init__(self, raw_url: str):
        self.type = None
        try:
            self._patterns = {
                "bilibili-video": {
                    "netloc": "www.bilibili.com",
                    "base_path": "/video",
                },
                "bilibili-bangumi": {
                    "netloc": "www.bilibili.com",
                    "base_path": "/bangumi/play",
                },
                # https://www.mute01.com/vodplay/2657-2-1.html
                "mutefun-video": {
                    "netloc": "www.mute01.com",
                    "base_path": "/vodplay",
                },
                "kugou-music": {
                    "netloc": "www.kugou.com",
                    "base_path": "/mixsong",
                },

            }

            raw_url = raw_url.strip("/")

            self.raw_url = raw_url
            self.parse_result = urllib.parse.urlparse(raw_url)
            self.netloc = self.parse_result.netloc
            self.path = self.parse_result.path.strip("/")
            self.base_path = os.path.dirname(self.path)
            self.sub_path = os.path.basename(self.path)
            self.scheme = self.parse_result.scheme
            print(self.path,self.base_path,self.sub_path,self.scheme)

            for key, value in self._patterns.items():
                if self.netloc == value["netloc"] and self.base_path.strip("/") == value["base_path"].strip("/"):
                    self.type = key
                    self.formatted_url = f"{self.scheme}://{self.netloc}/{self.path}"
                    return

            self.type = None
            self.formatted_url = None

        except Exception as e:
            print(e)
            self.type = None
            self.formatted_url = None

    def get_url(self):
        return self.formatted_url

    def get_type(self):
        return self.type

    def __eq__(self, other: 'FormattedUrl') -> bool:
        return self.formatted_url == other.formatted_url

    def get_index_in_driver(self, driver: webdriver) -> int:
        """
        获取当前页面在driver中的索引
        :param driver: webdriver
        :return: int, 若不存在则返回-1
        """
        for i, handle in enumerate(driver.window_handles):
            driver.switch_to.window(handle)
            # print(driver.current_url)
            url = FormattedUrl(driver.current_url)
            # print(url.formatted_url, self.formatted_url,url==self)
            if url == self:
                return i
        return -1

    def serialized(self):
        return {
            "type": self.get_type(),
            "formatted_url": self.get_url()
        }


    @staticmethod
    def Void():
        ret = FormattedUrl("")
        ret.type = None
        ret.formatted_url = None
        return ret


    @staticmethod
    def from_serialized(serialized: dict) -> 'FormattedUrl':
        if serialized["type"] is None and serialized["formatted_url"] is None:
            return FormattedUrl.Void()
        schema.Schema({
            "type": str,
            "formatted_url": str
        }).validate(serialized)
        ret = FormattedUrl(serialized["formatted_url"])
        if ret.get_type() != serialized["type"]:
            raise Exception("Type not match")
        return ret



class WD:
    _js_find_media_object = {
        # "bilibili-video": "$('video')",
        # "bilibili-bangumi": "$('video')",
        # "mutefun-video": """$("#playleft").find('iframe').contents().find("video")[0]""",
        # "kugou-music": "$('audio')",
        "bilibili-video": "document.querySelector('video')",
        "bilibili-bangumi": "document.querySelector('video')",
        "mutefun-video": """document.querySelector('#playleft').find('iframe').contents().find("video")[0]""",
        "kugou-music": "document.querySelector('video')",
    }

    def __init__(self, browser="firefox"):
        if browser == "edge":
            self.driver = webdriver.Edge()
        elif browser == "chrome":
            self.driver = webdriver.Chrome()
        elif browser == "firefox":
            self.driver = webdriver.Firefox()
        else:
            raise Exception("Invalid browser")

        # with open(os.path.abspath("../utils/jquery-3.7.1.min.js"), "r") as f:
        #     self.jquery_text = f.read

    def goto_page(self, url):
        try:
            url = url.replace("\\", "/")
            self.driver.execute_script(f"window.open('{url}')")
            self.driver.switch_to.window(self.driver.window_handles[-1])
        except Exception as e:
            self.driver.get(url)

    def get_state(self) -> (FormattedUrl, float, bool):
        """
        获取当前页面状态，返回页面类别，格式化页面URL对象，currentTime，paused
        :returns: (str,str,float,bool) 页面类别，格式化页面URL对象，currentTime，paused
        """
        self.driver.switch_to.window(self.driver.window_handles[-1])
        url = self.driver.current_url
        formatted_url = FormattedUrl(url)

        page_type = formatted_url.get_type()
        page_url = formatted_url.get_url()

        if page_type is None or page_url is None:
            return FormattedUrl.Void(), 0,False
        print(page_type)
        try:
            if page_type == "bilibili-video":
                # document.getElementByTagName('video')[0]
                media_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'video')))
            elif page_type == "bilibili-bangumi":
                # document.getElementByTagName('video')[0]
                media_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'video')))
            elif page_type == "mutefun-video":
                # document.getElementById('playleft').getElementsByTagName('iframe')[0].contentWindow.document.getElementsByTagName('video')[0].pause()
                playleft = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'playleft')))
                print(playleft)
                iframe = WebDriverWait(playleft, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'iframe')))

                print(iframe)
                self.driver.switch_to.frame(iframe)
                media_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'video')))
                print(media_element)
            elif page_type == "kugou-music":
                media_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'audio')))
                print(media_element)

            media_object = media_element

            currentTime = self.driver.execute_script(f"return arguments[0].currentTime", media_object)
            paused = self.driver.execute_script(f"return arguments[0].paused", media_object)
        except Exception as e:
            print(f"[{time.asctime()}, {os.path.basename(__file__)}] Function get_state() exception: {e}")
            return FormattedUrl.Void(), 0, False

        return formatted_url, currentTime, paused

    def sync_state(self, formatted_url: FormattedUrl, currentTime: float, paused: bool):
        """
        同步状态
        :param formatteed_url: 格式化页面URL对象
        :param currentTime: 当前时间
        :param paused: 是否暂停
        :return:
        """

        page_type = formatted_url.get_type()
        page_url = formatted_url.get_url()

        if page_type is None or page_url is None:
            return

        index = formatted_url.get_index_in_driver(self.driver)
        if index != -1:
            # self.driver.switch_to.window(self.driver.window_handles[index])
            pass
        else:

            self.goto_page(page_url)
            # self.driver.implicitly_wait(10)

        try:
            if page_type == "bilibili-video":
                # document.getElementByTagName('video')[0]
                media_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'video')))
            elif page_type == "bilibili-bangumi":
                # document.getElementByTagName('video')[0]
                media_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'video')))
            elif page_type == "mutefun-video":
                # document.getElementById('playleft').getElementsByTagName('iframe')[0].contentWindow.document.getElementsByTagName('video')[0].pause()
                playleft = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'playleft')))
                iframe = WebDriverWait(playleft, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'iframe')))
                self.driver.switch_to.frame(iframe)
                media_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'video')))
            elif page_type == "kugou-music":
                media_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'audio')))
            # js_find_media_object = WD._js_find_media_object.get(page_type)
            # js_find_media_object = f"return {js_find_media_object}" if not js_find_media_object.startswith(
            #     "return ") else js_find_media_object

            # print(page_url)
            # print(js_find_media_object)

            # media_object = self.driver.execute_script(js_find_media_object)
            media_object = media_element
            # print(media_object)
            self.driver.execute_script(f"arguments[0].currentTime = {currentTime}", media_object)
            if paused:
                self.driver.execute_script(f"arguments[0].pause()", media_object)
            else:
                self.driver.execute_script(f"arguments[0].play()", media_object)

        except Exception as e:
            print(f"[{time.asctime()}, {os.path.basename(__file__)}] Function sync_state() exception: {e}")
            return


if __name__ == "__main__":
    browser = WD(browser="firefox")
    browser.goto_page(f"file:///{os.path.abspath('../pages/start_up/index.html')}")
    # browser.goto_page("https://www.bilibili.com/video/BV1vx4y147cK")
    # browser.goto_page("https://www.bilibili.com/bangumi/play/ep333328")
    # browser.goto_page("https://www.mute01.com/vodplay/2657-2-1.html")
    # input()
    #
    # browser.sync_state(FormattedUrl("https://www.mute01.com/vodplay/2657-2-1.html"), 100, True)
    #
    # input()
    #
    # browser.sync_state(FormattedUrl("https://www.bilibili.com/video/BV1vx4y147cK"), 100, True)

    input()

    browser.sync_state(FormattedUrl("https://www.mute01.com/vodplay/2645-2-1.html"), 100, True)
