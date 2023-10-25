from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def login_hfut(driver):
    driver.get(
        'http://jxglstu.hfut.edu.cn/eams5-student/home')
    # 使用新教务登录，有的人的旧教务密码不正确
    login_new = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a.btn.btn-sx.btn-success[type="button"][href="/eams5-student/neusoft-sso/login"]'))
    )
    login_new.click()

    wait = WebDriverWait(driver, 5)

    account_input = wait.until(EC.presence_of_element_located((By.ID, 'username')))
    account_input.send_keys('2022217414')

    pwd_input = wait.until(EC.presence_of_element_located((By.ID, 'pwd')))
    pwd_input.send_keys('Yourloverczf23452.')

    account_login = wait.until(EC.presence_of_element_located((By.ID, 'sb2')))
    account_login.click()

    # 等待用户登录成功，进入教务系统
    WebDriverWait(driver, 1000).until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="icon-menu-title" and text()="我的课表"]'))
    )


    print('已成功登录，开始获取内容')
    # 等待元素出现
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='li-value']"))
    )

    # 获取元素的文本内容
    start_year = int(element.text)

    print("start_year:{}".format(start_year))
    class_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='icon-menu-title']"))
    )
    class_table.click()

    # 获取当前页面的句柄
    parent_window = driver.current_window_handle
    # 等待新窗口出现
    WebDriverWait(driver, 10).until(
        EC.number_of_windows_to_be(2)
    )
    # driver转到新页面
    all_windows = driver.window_handles
    new_window = [window for window in all_windows if window != parent_window][0]
    driver.switch_to.window(new_window)
    special_id = driver.current_url[-6:]
    # 注意关闭当前页面
    driver.close()
    driver.switch_to.window(parent_window)
    return special_id,start_year

