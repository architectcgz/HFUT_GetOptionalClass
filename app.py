from flask import Flask, render_template, request
from utils.getOptionalClass import GetOptionalClass

app = Flask(__name__)


@app.route('/index/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/optional/courses/', methods=['GET'])
def run_function():
    browser_type = request.args.get('info')
    print(browser_type)
    s = GetOptionalClass(browser_type)
    print('数据获取完成，向前端传递')
    return render_template('optional_courses.html',
                           courseList=s.optionalCourseList,
                           suggestion=s.opCourseSuggestion.split('\n'))


if __name__ == '__main__':
    print('请在浏览器中输入下面的网址: http://127.0.0.1:5000/index')
    app.run()
