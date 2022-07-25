import requests
import json
from requests import utils
import re


def encrypt(pwd="", aeskey=""):
    """
    :param pwd: 密码明文
    :param aeskey: 密钥
    :return: 密文
    """
    jsurl = "https://ids.xidian.edu.cn/authserver/xidianNewThemecs/static/common/encrypt.js?v=20220524.104802"
    # 获取加密用的js代码
    a = requests.get(jsurl)
    js_code = a.text
    import execjs
    js_compiled = execjs.compile(js_code)

    result = js_compiled.call("encryptPassword", pwd, aeskey)
    # print(result)
    return result


def login(id, pwd):
    """
    说实话有些过于麻烦了,那几次302分开写主要是为了获取全部的cookie
    :param id: 学号
    :param pwd: 密码
    :return: cookie
    """
    # 构造表单
    form = {
        "username": id,
        "rememberMe": "true",
        "_eventId": "submit",
        "cllt": "userNameLogin",
        "dllt": "generalLogin"
    }
    form["execution"], pwdEncryptSalt, cookie = get_sth()
    form["password"] = encrypt(pwd=pwd, aeskey=pwdEncryptSalt)

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62"
    }

    # 一站式大厅
    url = "https://ids.xidian.edu.cn/authserver/login?service=http%3A%2F%2Fehall.xidian.edu.cn%2Flogin%3Fservice%3Dhttp%3A%2F%2Fehall.xidian.edu.cn%2FappShow%3FappId%3D4768574631264620"

    # 查询是否需要验证码,如果需要可以考虑用ddddocr解决
    if checkNeedCaptcha(id):
        print("需要验证码,暂时无法解决，润了")
        quit()

    cookie_dict = {}

    # 第一次请求,会发生302重定向
    res = requests.post(url, params=form, headers=header, cookies=cookie, allow_redirects=False)
    c_d1 = requests.utils.dict_from_cookiejar(res.cookies)  # c_d1就是第一次的cookie

    # 构造第二次请求需要的url和cookies
    u2 = res.headers['location']
    c2 = res.cookies

    # 第二次302重定向
    res2 = requests.get(u2, cookies=c2, allow_redirects=False)
    c_d2 = requests.utils.dict_from_cookiejar(res2.cookies)

    # 构造第三次请求需要的url和cookies
    u3 = res2.headers['location']
    c3 = res2.cookies

    # 第三次302重定向
    res3 = requests.get(u3, cookies=c3, allow_redirects=False)
    c_d3 = requests.utils.dict_from_cookiejar(res3.cookies)

    # 合并前几次的所有cookie
    c_d = {}
    for i in cookie:
        c_d[i] = cookie[i]
    for i in c_d1:
        c_d[i] = c_d1[i]
    for i in c_d2:
        c_d[i] = c_d2[i]
    for i in c_d3:
        c_d[i] = c_d3[i]

    # 构造第四次请求需要的url和cookies
    u4 = res3.headers['location']
    c4 = c_d

    # 第四次302重定向
    res4 = requests.get(u4, cookies=c4, allow_redirects=False)
    c_d4 = requests.utils.dict_from_cookiejar(res4.cookies)

    # 再次整合cookie
    for i in c_d4:
        c_d[i] = c_d4[i]

    # 最后一次请求,此时的地址已经含有gid_
    all = requests.get(res4.headers['location'], cookies=c_d, allow_redirects=False)

    c_dend = requests.utils.dict_from_cookiejar(all.cookies)

    # 最终的cookie
    for i in c_dend:
        c_d[i] = c_dend[i]

    return c_d


def get_sth():
    """
    获得所需的execution和pwdEncryptSalt(aesKey)
    :return:
    """
    # 一站式大厅的登录界面
    url = "https://ids.xidian.edu.cn/authserver/login?service=http%3A%2F%2Fehall.xidian.edu.cn%2Flogin%3Fservice%3Dhttp%3A%2F%2Fehall.xidian.edu.cn%2FappShow%3FappId%3D4768574631264620"

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36 Edg/103.0.1264.44",
    }
    rule_execution = re.compile(r'name="execution"(.*?)>')
    rule_pwdEncryptSalt = re.compile(r'id="pwdEncryptSalt"(.*?)>')

    res = requests.get(url, header)

    execution = re.findall(rule_execution, res.text)
    pwdEncryptSalt = re.findall(rule_pwdEncryptSalt, res.text)

    return execution[0][:-3][8:], pwdEncryptSalt[0][8:][:-3], requests.utils.dict_from_cookiejar(res.cookies)


def checkNeedCaptcha(userid=""):
    url = "https://ids.xidian.edu.cn/authserver/checkNeedCaptcha.htl?username=" + userid
    res = requests.get(url)
    # print(res.text)
    if "true" in res.text:
        return 1
    elif "false" in res.text:
        return 0


def get_msg(cookie):
    """
    查询成绩
    :param cookie: 最少包含_WEU和MOD_AUTH_CAS
    :return:
    """
    url = "https://ehall.xidian.edu.cn/jwapp/sys/cjcx/modules/cjcx/xscjcx.do"
    # with open("form2.json", "r", encoding="utf-8") as f:
    #     form = json.load(f)
    form = {
        "querySetting": [
            {
                "name": "SFYX",
                "caption": "是否有效",
                "linkOpt": "AND",
                "builderList": "cbl_m_List",
                "builder": "m_value_equal",
                "value": "1",
                "value_display": "是"
            }
        ],
        "*order": "-XNXQDM,-KCH,-KXH",
        "pageSize": 100,
        "pageNumber": 1
    }
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62"
    }
    # cookie = {
    #     '_WEU': 'SMarqT38YcXZOlKFQL0aqo5R2XNhMD4yZ0SRUUV3wvyCU4nOJ5nBLweWYOmT7MvVt*NqHyzsTGIQosoue5wDrhkQovvblEjNPBqb1t1B4sL.',
    #     'MOD_AUTH_CAS': 'MOD_AUTH_ST-646296-Z8kTKtMm3GmLWQrc8hh-YfyZKdoauthserver5'
    # }
    # 最少要有上面这俩玩意

    a = requests.get(url, params=form, headers=header, cookies=cookie)

    with open("grades.json", "wb") as f:
        f.write(a.content)

    with open("grades.json", "r", encoding="utf-8") as f:
        grades = json.load(f)
    #
    print(grades["datas"]["xscjcx"]["extParams"]["msg"])
    print("共:", grades["datas"]["xscjcx"]["totalSize"], "条数据")
    print("数据更新成功,保存在grade.json文件中")

    # for i in ress["datas"]["xscjcx"]["rows"]:
    #     print(i["XSKCM"],i["ZCJ"])


if __name__ == '__main__':
    print("加载用户配置")
    with open("config.json", "r") as c:
        config = json.load(c)
    userid = config["username"]
    passwd = config["password"]

    try:
        with open("cookie.json", "r") as c:
            cookie_all = json.load(c)
    except:
        print("something about cookie error ...")
        cookie_all = {}
    if userid in cookie_all:
        print("已有cookie,直接查询")
        cookie = cookie_all[userid]
        flag = 0
    else:
        print("即将登录")
        flag = 1
        try:
            cookie = login(userid, passwd)
        except:
            print("登录失败，请重新登录")
            cookie = {}
            quit()

    get_msg(cookie)
    if flag == 1 and config["if_save_cookie"] == "1":
        cookie_all[userid] = cookie
        with open("cookie.json", "w") as c:
            c.write(json.dumps(cookie_all))
        print("cookie保存成功")
