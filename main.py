import datetime
import os.path
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


# 首先打开登录页面拿到sessionID
def login(driver):
    driver.get('http://jxglstu.hfut.edu.cn/eams5-student/home')
    WebDriverWait(driver, 1000).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='menu-group-title' and @data-v-04f76387]"))
    )

    print('已成功登录，开始获取内容')
    class_table = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='icon-menu-title']"))
    )
    class_table.click()
    # Get the current window handle
    parent_window = driver.current_window_handle
    # Wait for the new window to appear (modify the timeout as needed)
    WebDriverWait(driver, 10).until(
        EC.number_of_windows_to_be(2)
    )
    # Switch to the new window
    all_windows = driver.window_handles
    new_window = [window for window in all_windows if window != parent_window][0]
    driver.switch_to.window(new_window)
    special_id = driver.current_url[-6:]
    # 注意关闭当前页面
    driver.close()
    driver.switch_to.window(parent_window)
    return special_id
    # 下面是之前写的自动登录的代码，主要是如果输入错误密码或学号会出现验证码，还没学会自动识别验证码
    # wait = WebDriverWait(driver, 5)
    #
    # account_input = wait.until(EC.presence_of_element_located((By.ID, 'u')))
    # account_input.send_keys(id)
    #
    # pwd_input = wait.until(EC.presence_of_element_located((By.ID, 'p')))
    # pwd_input.send_keys(password)
    #
    # account_login = wait.until(EC.presence_of_element_located((By.ID, 'submit')))
    # account_login.click()


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


def getOneSemester(driver, website):
    driver.get(website)
    # 点击‘全部课程’
    total_courses = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, 'lessons'))
    )
    total_courses.click()
    # 等待course table加载完成
    # get the HTML content of the page
    html_content = driver.page_source
    # use BeautifulSoup to parse the HTML
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
    cls_name_format = re.compile(r'<p class="\w+">(?P<className>[\w\s\u4e00-\u9fa5（）]+)</p>')
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
        print(f'第{semester_count}学期的课程数据已成功获取')
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


def SortClasses(lst):
    common_class = []  # 通识必修课
    professional_class = []  # 专业必修课
    professional_elective = []  # 专业选修
    chosen_class = []  # 选修
    other_class = []  # 其他
    for i in lst:
        for j in i:
            if j[1] == '通识必修课':
                common_class.append(j)
            elif j[1] == '学科基础和专业必修课':
                professional_class.append(j)
            elif j[1] == '各专业选修课':
                professional_elective.append(j)
            elif j[1][0:2] == '公选' or j[1][0:2:] == '慕课':
                chosen_class.append(j)
            else:
                other_class.append(j)
    dict = {'通识必修课': common_class, '学科基础和专业必修课': professional_class,
            '各专业选修课': professional_elective, '公选和慕课': chosen_class, '其他': other_class}
    return dict


def WriteToFile(lst):
    result = SortClasses(lst)
    # 将文件保存在当前的目录下
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open('classes.txt', 'a') as f:
        for key, value in result.items():
            f.write(f'{key}:')
            for i in value:
                f.write(f'{i}, ')
            f.write('\n')


def orgraniseNext(exist_class_list):
    all_class_set = {'哲学、历史与心理学', '文化、语言与文学', '经济、管理与法律', '自然、环境与科学', '信息、技术与工程',
                     '艺术、体育与健康', '就业、创新与创业',
                     '社会、交往与礼仪', '人生规划、品德与修养'}
    cls_set = set()  # 当前选修过的课程名集合
    credits = 0  # 当前的选修学分
    for cls in exist_class_list:
        cls_set.add(cls[1][3::])
        credits += float(cls[2])
    if credits < 12:
        print(f'当前你的通识教育选修学分为{credits},不足12学分')
        if len(cls_set) >= 6:
            print('你的选修模块已满足6个，可选修所有模块的任意课程，来补足学分')
        else:
            print(
                f'你的选修模块不足6个，请在以下模块{all_class_set - cls_set}中继续选修{6 - len(cls_set)}个模块的课程，补足选修模块和学分')
    elif credits >= 12 and len(cls_set) >= 6:
        print('恭喜你的同时教育选修课已满足毕业要求')
    else:
        print(
            f'你的通识教育选修学分已达到12分，但你的选修模块为{len(cls_set)}个,不足6个，请在以下模块{all_class_set - cls_set}'
            f'中继续选修{6 - len(cls_set)}个模块的课程，补足选修模块')


def main():
    driver = webdriver.Edge()
    special_id = login(driver)
    result = getOptionalCourseList(getAll(driver, special_id))
    print('你选修过的课程如下:')
    print(result)
    print()
    orgraniseNext(result)
    driver.quit()
    input('输入任意字符退出...')


if __name__ == main():
    main()
