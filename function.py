import datetime
import re
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from login import login_hfut


def getStartYear(driver, special_id):
    # 转到课表
    driver.get(f'http://jxglstu.hfut.edu.cn/eams5-student/for-std/course-table/info/{special_id}')
    WebDriverWait(driver, 5)
    # 获取页面内容(起始学期)
    html_content = driver.page_source
    # use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    # 注释下是浏览器不隐藏状态下的获取h2标签内容的方法
    h2_tag = soup.find('h2', class_='info-title')
    info = h2_tag.get_text(strip=True)
    start_index = info.index('(') + 1
    # 获取如2022这样的入学年份
    start_year = info[start_index:start_index + 4:]
    return int(start_year)


def getOneSemester(driver, url):
    driver.get(url)
    html_content = driver.page_source
    # 使用BeautifulSoup转化html
    soup = BeautifulSoup(html_content, 'html.parser')
    # 找到id为lessons的table标签
    table = soup.find('table', {'id': 'lessons'})
    # 找到所有的tr标签行
    rows = table.find_all('tr')

    class_detail = []
    for row in rows:
        # 找到该行的第一个td标签
        class_info = row.find('td')
        if class_info:
            # 取得td标签中的p标签中的前三个有用的p标签
            class_detail.append(class_info.find_all('p'))
    # 已经获取到所有class 的list
    lst_result = []
    cls_name_format = re.compile(r'<p class="\w+">(?P<course_name>[\w\s\u4e00-\u9fa5（）:《》、：()]+)</p>')
    cls_course_format = re.compile(
        r'<p>\w+<i class="operator"></i>(?P<course_nature>[\u4e00-\u9fa5-、]+)<i class="operator">')
    cls_course_score_format = re.compile(
        r'<p><span class="span-gap">[\u4e00-\u9fa5]+\((?P<course_score>[\d.]+)\)</span>')
    lst_formats = [cls_name_format, cls_course_format, cls_course_score_format]

    for i in range(len(class_detail)):
        lst_result.append([])
        for j in range(3):
            text_content = str(class_detail[i][j])
            match = lst_formats[j].match(text_content)
            if match:
                lst_result[i].append(match.group(1))
    return lst_result


def getAll(driver, special_id):
    start_year = getStartYear(driver, special_id)
    website = 'http://jxglstu.hfut.edu.cn/eams5-student/for-std/course-table/info/all-courses?semesterId={}&dataId={}'
    start_semester_id = 114 + (start_year - 2020) * 2 * 20
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
        url = website.format(now_semester_id, special_id)
        result.append(getOneSemester(driver, url))
        # print(f'第{semester_count}学期的课程数据已成功获取')
        # 防止速度过快发生You have sent too many requests in a given amount of time.
        #time.sleep(1)
        semester_count += 1
        now_semester_id += 20
    return result


def getOptionalCourseList(lst):
    result = []
    for semesters in lst:
        for classes in semesters:
            if classes[1][0:2] == '公选' or classes[1][0:2:] == '慕课':
                result.append(classes)

    return result


def organiseNext(exist_class_list):
    all_class_set = {'哲学、历史与心理学', '文化、语言与文学', '经济、管理与法律', '自然、环境与科学', '信息、技术与工程',
                     '艺术、体育与健康', '就业、创新与创业', '社会、交往与礼仪', '人生规划、品德与修养'}
    cls_set = set()  # 当前选修过的课程名集合
    credits = 0  # 当前的选修学分
    for cls in exist_class_list:
        cls_set.add(cls[1][3::])
        credits += float(cls[2])
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



def execute():
    driver = webdriver.Edge()
    special_id = login_hfut(driver)

    result = getOptionalCourseList(getAll(driver, special_id))
    print()
    organise_next = organiseNext(result)
    driver.quit()

    print(result)
    print('---')
    print(organise_next)
    print('---')
    return organise_next,result
