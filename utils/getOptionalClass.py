import concurrent.futures
import datetime
import json
import time

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver


class GetOptionalClass:
    def __init__(self):
        self.__driver = webdriver.Edge()
        # 请求头 包含user-agent和cookie 由login_hfut获取
        self.__headers = {}
        self.__special_id, self.__start_year = self.__login_hfut()
        # 退出driver
        self.__driver.quit()
        start1 = time.time()
        self.optionalCourseList = self.__get_optional_courses()
        end1 = time.time()
        print('选修课程列表获取完成，用时{}'.format(end1-start1))
        self.opCourseSuggestion = self.__organiseNext()
        print(self.opCourseSuggestion)


    def __login_hfut(self):
        self.__driver.get(
            'http://jxglstu.hfut.edu.cn/eams5-student/home')
        # 使用新教务登录，有的人的旧教务密码不正确
        login_new = WebDriverWait(self.__driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a.btn.btn-sx.btn-success[type="button"][href="/eams5-student/neusoft-sso/login"]'))
        )
        login_new.click()

        wait = WebDriverWait(self.__driver, 5)

        account_input = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        account_input.send_keys('2022217414')

        pwd_input = wait.until(EC.presence_of_element_located((By.ID, 'pwd')))
        pwd_input.send_keys('Yourloverczf23452.')

        account_login = wait.until(EC.presence_of_element_located((By.ID, 'sb2')))
        account_login.click()

        # 等待用户登录成功，进入教务系统
        WebDriverWait(self.__driver, 1000).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="icon-menu-title" and text()="我的课表"]'))
        )

        print('已成功登录，开始获取内容')
        # 等待元素出现
        element = WebDriverWait(self.__driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='li-value']"))
        )

        # 获取元素的文本内容
        start_year = int(element.text)

        class_table = WebDriverWait(self.__driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='icon-menu-title']"))
        )
        class_table.click()

        # 获取当前页面的句柄
        parent_window = self.__driver.current_window_handle
        # 等待新窗口出现
        WebDriverWait(self.__driver, 10).until(
            EC.number_of_windows_to_be(2)
        )
        # driver转到新页面
        all_windows = self.__driver.window_handles
        new_window = [window for window in all_windows if window != parent_window][0]
        self.__driver.switch_to.window(new_window)
        # 获取special_id
        special_id = self.__driver.current_url[-6:]

        # 获取User-Agent
        user_agent = self.__driver.execute_script('return navigator.userAgent')
        self.__headers['User-Agent'] = user_agent
        # 获取cookie
        cookies = self.__driver.get_cookies()
        # 组装cookie
        cookie = ''.join([f'{cookie["name"]}={cookie["value"]};' for cookie in cookies])
        self.__headers['Cookie'] = cookie
        # 注意关闭当前页面
        self.__driver.close()
        self.__driver.switch_to.window(parent_window)
        # 关闭最后的页面
        self.__driver.close()

        # 关闭页面，退出Driver 便于后续爬取课程数据
        return special_id, start_year

    def __calculate_end_semester_id(self):
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        if 2 <= month <= 7:
            return ((year - 2020) * 2 - 1) * 2 * 20 + 114
        else:
            if year % 2 == 0:
                return (year - 1 - 2020) * 2 * 20 + 114
            else:
                return (year - 2020) * 2 * 20 + 114

    def __fetch_course_data(self, semester_id, special_id):
        url = 'http://jxglstu.hfut.edu.cn/eams5-student/for-std/course-table/get-data?bizTypeId=23&semesterId={}&dataId={}'.format(
            semester_id, special_id)
        return self.__get_courses_one_semester(url)

    def __get_optional_courses(self):
        start_semester_id = 114 + (self.__start_year - 2020) * 2 * 20
        end_semester_id = self.__calculate_end_semester_id()

        result = []
        semester_count = 1

        # 使用线程池来同时获取每个学期的课程数据
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.__fetch_course_data, semester_id, self.__special_id): semester_id
                for semester_id in range(start_semester_id, end_semester_id + 1, 20)}

            for future in concurrent.futures.as_completed(futures):
                this_semester_course = future.result()
                if this_semester_course:
                    result.append(this_semester_course)
                print(f'第{semester_count}学期的课程数据已成功获取')
                semester_count += 1
            # 将三维数据转化为二维的
            result1 = sum(result,[])
            print(result1)
        return result1

    def __get_courses_one_semester(self, url):
        # 每次都需要带着请求头请求
        response = requests.get(url, headers=self.__headers)
        html_content = response.text
        # data是dict类型的
        data = json.loads(html_content)
        lst_result = []
        for item in data['lessons']:
            if item['courseType']['nameZh'][0:2] == '慕课' or item['courseType']['nameZh'][0:2] == '公选':
                lst_result.append([item['course']['nameZh'], item['course']['credits'], item['courseType']['nameZh']])
        return lst_result

    def __organiseNext(self):
        all_class_set = {
            '哲学、历史与心理学', '文化、语言与文学', '经济、管理与法律', '自然、环境与科学',
            '信息、技术与工程', '艺术、体育与健康', '就业、创新与创业',
            '社会、交往与礼仪', '人生规划、品德与修养'
        }

        cls_set = set(course[2][3::] for course in self.optionalCourseList)
        credits = sum(course[1] for course in self.optionalCourseList)

        result = f'当前你的通识教育选修学分为 {credits}, 不足 12 学分\n'

        if credits < 12:
            if len(cls_set) >= 6:
                result += '你的选修模块已满足 6 个，可选修所有模块的任意课程，来补足学分'
            else:
                remaining_modules = 6 - len(cls_set)
                remaining_modules_set = all_class_set - cls_set
                result += f'你的选修模块为 {len(cls_set)} 个, 不足 6 个，请在以下模块 {remaining_modules_set} 中继续选修 {remaining_modules} 个模块的课程，补足选修模块和学分'
        elif credits >= 12 and len(cls_set) >= 6:
            result = '恭喜你的通识教育选修课已满足毕业要求'
        else:
            remaining_modules = 6 - len(cls_set)
            remaining_modules_set = all_class_set - cls_set
            result = f'你的通识教育选修学分已达到 12 分，但你的选修模块为 {len(cls_set)} 个, 不足 6 个，请在以下模块 {remaining_modules_set} 中继续选修 {remaining_modules} 个模块的课程，补足选修模块'

        return result

