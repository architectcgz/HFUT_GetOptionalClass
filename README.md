# GetOptionalClass
此脚本可以获取当前你选修过的通识教育选修课，并显示学分，课程类型等；还可提出对接下来选修课程的建议。
在main/dist文件夹中有一个main.exe文件，下载后可以直接使用。
运行main.exe后，其会打开Flask服务，在浏览器中输入http://127.0.0.1:5000/index 即可看到说明页面
点击获取按钮会自动打开Edge浏览器，并打开HFUT教务系统界面。
在教务系统中输入学号和密码即可登录成功。
之后该脚本会自动获取选修过的课程，并在浏览器中显示结果。
 
如果不需要通过网页查看结果 请转到master分支下载getOptionalClass.py代码使用，也推荐这样使用，因为从后端传递到网页前端需要花费额外的时间。
代码运行需要安装 selenium、requests、json、time、datetime等库
