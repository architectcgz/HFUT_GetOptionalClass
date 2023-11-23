import datetime
import json
import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver


class GetOptionalClass:
    def __init__(self, browser_type):
        if browser_type == 'Firefox':
            self.__driver = webdriver.Firefox()
        elif browser_type == 'Chrome':
            self.__driver = webdriver.Chrome()
        # 因为大多数同学用的windows都自带Edge
        else:
            self.__driver = webdriver.Edge()
        # 请求头 包含user-agent和cookie,由login_hfut获取 User-Agent默认为Edge的
        self.__headers = {}
        self.__special_id, self.__start_year = self.login_hfut()

        start1 = time.time()
        self.optionalCourseList = self.__get_optional_courses()
        end1 = time.time()
        print('选修课程列表获取完成，用时{}'.format(end1 - start1))
        self.opCourseSuggestion = self.__organiseNext()

    def login_hfut(self):
        # 使用新教务登录，有的人的旧教务密码不正确
        
        self.__driver.get(
            'https://cas.hfut.edu.cn/cas/login?service=http%3A%2F%2Fjxglstu.hfut.edu.cn%2Feams5-student%2Fneusoft-sso%2Flogin')

        # 等待用户登录成功，进入教务系统

        WebDriverWait(self.__driver, 1000).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="icon-menu-title" and text()="我的课表"]'))
        )


        print('已成功登录,开始获取内容,请稍作等待')
        # 等待元素出现
        element = WebDriverWait(self.__driver, 10).until(
            
             EC.presence_of_element_located((By.XPATH, "//div[@class='li-key' and text()='年级']/following-sibling::div[@class='li-value']"))
        )

        # 获取元素的文本内容
        start_year = int(element.text)

        # 如果输入学生号和密码的页面不全屏，或者未加载完成，会出现遮挡的现象，使用以下方法处理
        # 等待遮挡元素不可见
        WebDriverWait(self.__driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//div[@class='el-loading-spinner']")))

        # 执行操作
        class_table = WebDriverWait(self.__driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='icon-menu-icon']"))
        )
        class_table.click()

        # 获取User-Agent
        user_agent = self.__driver.execute_script('return navigator.userAgent;')
        self.__headers['User-Agent'] = user_agent

        # 提前获取Cookie 不要在课表页面进行获取 FireFox无法从课表页面获取Cookie!
        cookies = self.__driver.get_cookies()
        # 组装cookie
        cookie = ''.join([f'{cookie["name"]}={cookie["value"]};' for cookie in cookies])
        self.__headers['Cookie'] = cookie
        
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

        # 设置防盗链 表示从学校网站跳转到的
        self.__headers['Referer'] = 'http://jxglstu.hfut.edu.cn/eams5-student/for-std/course-table/info/{}'.format(special_id)

        # 注意关闭当前页面
        self.__driver.close()
        self.__driver.switch_to.window(parent_window)
        # 关闭最后的页面
        self.__driver.close()
        # driver已经不再需要，退出driver
        self.__driver.quit()
        # 释放掉driver的内存
        del self.__driver
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
        for semester_id in range(start_semester_id, end_semester_id + 1, 20):
            this_semester_course = self.__fetch_course_data(semester_id, self.__special_id)
            if this_semester_course:
                result.append(this_semester_course)
            print(f'第{semester_count}学期的课程数据已成功获取')
            semester_count += 1
            # 将三维信息[总信息[每一个学期的信息[课程信息]]]转化为二维
        result1 = sum(result, [])
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

        # 选修过的课程的类型集合
        cls_set = set(course[2][3::] for course in self.optionalCourseList)
        # 统计学分
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

if __name__ == "__main__":
    browser = input('请输入你电脑装有的浏览器(Edge-微软/Chrome-谷歌/Firefox-火狐)\n输入英文即可，如输入Edge:')
    # 只需实例化getOptionalClass类，其余都将自动操作
    getOptionalClass = GetOptionalClass(browser_type=browser)
    print("你选修过的课程有:")
    print(getOptionalClass.optionalCourseList)
    print("你可以参考一下选修建议:\n"+getOptionalClass.opCourseSuggestion)
