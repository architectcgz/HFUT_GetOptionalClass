from flask import Flask, render_template
from utils.getOptionalClass import GetOptionalClass

app = Flask(__name__)


@app.route('/index/')
def index():
    return render_template('index.html')


@app.route('/optional/courses/', methods=['GET'])
def run_function():
    s = GetOptionalClass()
    print('数据获取完成，向前端传递')
    return render_template('optional_courses.html', courseList=s.optionalCourseList, suggestion=s.opCourseSuggestion)


if __name__ == '__main__':
    app.run()
