from flask import Flask, render_template, jsonify
from function import execute

app = Flask(__name__)


@app.route('/index/')
def index():
    return render_template('index.html')


@app.route('/run/function/', methods=['POST'])
def run_function():
    return jsonify(result=execute())


if __name__ == '__main__':
    app.run()
