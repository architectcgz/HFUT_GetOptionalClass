import datetime
import json
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
        self.__courses = self.__get_all_courses()
        self.optionalCourseList = self.__getOptionalCourses(self.__courses)
        self.opCourseSuggestion = self.__organiseNext(self.optionalCourseList)
        # 退出driver
        self.__driver.quit()

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
        # 退出driver
        self.__driver.quit()

        # 关闭页面，退出Driver 便于后续爬取课程数据
        return special_id, start_year

    def __get_courses_one_semester(self, url):
        # 每次都需要带着请求头请求
        response = requests.get(url, headers=self.__headers)
        html_content = response.text
        # data是dict类型的
        data = json.loads(html_content)
        lst_result = []
        for item in data['lessons']:
            lst_result.append([item['course']['nameZh'], item['course']['credits'], item['courseType']['nameZh']])
        print(lst_result)
        return lst_result

    def __get_all_courses(self):
        website = 'http://jxglstu.hfut.edu.cn/eams5-student/for-std/course-table/get-data?bizTypeId=23&semesterId={}&dataId={}'
        start_semester_id = 114 + (self.__start_year - 2020) * 2 * 20
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        if 2 <= month <= 7:
            end_semester_id = ((year - 2020) * 2 - 1) * 2 * 20 + 114
        else:
            if year % 2 == 0:
                end_semester_id = (year - 1 - 2020) * 2 * 20 + 114
            else:
                end_semester_id = (year - 2020) * 2 * 20 + 114
        now_semester_id = start_semester_id
        result = []
        semester_count = 1
        while now_semester_id <= end_semester_id:
            url = website.format(now_semester_id, self.__special_id)
            result.append(self.__get_courses_one_semester(url))
            print(f'第{semester_count}学期的课程数据已成功获取')
            # 防止速度过快发生You have sent too many requests in a given amount of time.
            # time.sleep(1)
            semester_count += 1
            now_semester_id += 20
        return result

    def __getOptionalCourses(self, lst):
        """
        从所有课程list中得到选修课的list
        :param lst:所有课程的列表
        :return:
        """
        result = []
        for semesters in lst:
            for classes in semesters:
                if classes[2][0:2] == '公选' or classes[2][0:2] == '慕课':
                    result.append(classes)
        return result

    def __organiseNext(self, exist_class_list):
        all_class_set = {'哲学、历史与心理学', '文化、语言与文学', '经济、管理与法律', '自然、环境与科学',
                         '信息、技术与工程',
                         '艺术、体育与健康', '就业、创新与创业', '社会、交往与礼仪', '人生规划、品德与修养'}
        cls_set = set()  # 当前选修过的课程名集合
        credits = 0  # 当前的选修学分
        for cls in exist_class_list:
            cls_set.add(cls[2][3::])
            credits += cls[1]
        result = ''
        if credits < 12:
            result += f'当前你的通识教育选修学分为{credits},不足12学分\n'
            if len(cls_set) >= 6:
                result += '你的选修模块已满足6个，可选修所有模块的任意课程，来补足学分'
            else:
                result += f'你你的选修模块为{len(cls_set)}个,不足6个，请在以下模块{all_class_set - cls_set}中继续选修{6 - len(cls_set)}个模块的课程，补足选修模块和学分'
        elif credits >= 12 and len(cls_set) >= 6:
            result += '恭喜你的通识教育选修课已满足毕业要求'
        else:
            result += f'你的通识教育选修学分已达到12分，但你的选修模块为{len(cls_set)}个,不足6个，请在以下模块{all_class_set - cls_set}' \
                      f'中继续选修{6 - len(cls_set)}个模块的课程，补足选修模块'
        return result
