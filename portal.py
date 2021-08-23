import requests
import threading
import numpy as np
import cv2
import time
from datetime import datetime

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

from pred import pred_captcha

class Portal:
    def __init__(self, lock = None):
        self._re = requests.session()
        self._lock = lock
        self._reg_courses_code = []
        self._drop_courses_code = []

        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self._proxies = {
            "http": "socks5://127.0.0.1:8080",
            "https": "socks5://127.0.0.1:8080",
        }
        self._login_page = 'https://portal.aut.ac.ir/aportal/login.jsp'
        self._captcha_page = 'https://portal.aut.ac.ir/aportal/PassImageServlet'
        self._cs_page = 'https://portal.aut.ac.ir/aportal/regadm/student.portal/student.portal.jsp?action=edit&st_info=register&st_sub_info=u_mine_all'
        self._reg_page = 'https://portal.aut.ac.ir/aportal/regadm/student.portal/student.portal.jsp?action=apply_reg&st_info=add'
        self._drop_page = 'https://portal.aut.ac.ir/aportal/regadm/student.portal/student.portal.jsp?action=apply_reg&st_info=drop'
    

    def login(self, user, pazz, sleep_seconds=0):
        payload = {
            "username": user,
            "password": pazz,
            "passline": ""
        }
        resp = self._re.post(self._login_page, headers=self._headers, data=payload, allow_redirects=False)

        while True:
            payload["passline"] = self._solve_login_captcha()
            resp = self._re.post(self._login_page, headers=self._headers, data=payload, allow_redirects=False)
            text = resp.text

            if text.__contains__("اطلاعات وارد شده نامعتبر"):
                return False
            elif resp.status_code == 200 and (not text.__contains__("ورود کاربران")):
                Portal.print_with_time("Logged in.")
                return True
            if text.__contains__("حروف تصویر"):
                Portal.print_with_time("wrong captcha")
            else:
                Portal.print_with_time("not opened yet or 503")
            time.sleep(sleep_seconds)
    

    def do_course_selection(self):
        # Dropping courses
        while self._drop_courses_code:
            self._drop_course(self._drop_courses_code.pop(0))
        
        # Registering courses
        while self._reg_courses_code:
            self._register_course(self._reg_courses_code.pop(0))


    def _register_course(self, code):
        payload = {
            'st_reg_course': code,
            # 'addpassline': self._solve_cs_captcha(),
            'st_course_add': 'درس را اضافه کن'
        }
        while True:
            payload['addpassline'] = self._solve_cs_captcha()
            resp = self._re.post(self._reg_page, headers=self._headers, data=payload)
            # print(resp.text.strip())
            if resp.status_code == 200 and (not resp.text.__contains__("فيلد حروف تصوير معتبر")):
                break
            print("wrong captcha or 503")
        Portal.print_with_time(f"{code} registered")


    def _drop_course(self, code):
        payload = {
            'st_reg_course': code,
            'st_course_drop': 'درس انتخابي را حذف کن',
            'st_comments1': '',
            'addpassline': '',
            'st_reg_groupno': '',
            'st_reg_courseid': '',
        }
        while True:
            resp = self._re.post(self._drop_page, headers=self._headers, data=payload)
            # print(resp.text.strip())
            if resp.status_code == 200:
                break
            print("503")
        Portal.print_with_time(f"{code} dropped")


    def add_reg_course(self, code):
        if isinstance(code, str):
            self._reg_courses_code.append(code)

    
    def add_drop_course(self, code):
        if isinstance(code, str):
            self._drop_courses_code.append(code)
            
    
    def _get_captcha(self):
        try:
            resp = self._re.get(self._captcha_page, headers=self._headers)
            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            captcha_image = cv2.imdecode(arr, -1)

            return captcha_image
        except Exception as e:
            print(e)
    

    def _solve_login_captcha(self):
        return self._solve_captcha(5)


    def _solve_cs_captcha(self):
        self._re.get(self._cs_page, headers=self._headers, allow_redirects=False)
        return self._solve_captcha(2)


    def _solve_captcha(self, words):
        captcha_image = None
        while captcha_image is None:
            captcha_image = self._get_captcha()

        if self._lock is not None:
            with self._lock:
                text = pred_captcha(captcha_image, words)
        else:
            text = pred_captcha(captcha_image, words)
        
        # print(text)
        return text
    
    @staticmethod
    def print_with_time(txt):
        c_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"[{c_time_str}] {txt}")
