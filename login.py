from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def login_hfut(driver):
    driver.get(
        'http://cas.hfut.edu.cn/cas/login?service=http%3A%2F%2Fjxglstu.hfut.edu.cn%2Feams5-student%2Fneusoft-sso%2Flogin')
    # 等待用户登录成功，进入教务系统
    WebDriverWait(driver, 1000).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='menu-group-title' and @data-v-04f76387]"))
    )
    # wait = WebDriverWait(driver, 5)
    #
    # account_input = wait.until(EC.presence_of_element_located((By.ID, 'username')))
    # account_input.send_keys('2022217414')
    #
    # pwd_input = wait.until(EC.presence_of_element_located((By.ID, 'pwd')))
    # pwd_input.send_keys('Yourloverczf23452.')
    #
    # account_login = wait.until(EC.presence_of_element_located((By.ID, 'sb2')))
    # account_login.click()

    print('已成功登录，开始获取内容')
    class_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='icon-menu-title']"))
    )
    class_table.click()
    # class_table = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.XPATH, "//div[@class='icon-menu-title']"))
    # )
    # ActionChains(driver).move_to_element(class_table).click().perform()
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

