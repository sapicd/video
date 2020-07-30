# -*- coding: utf-8 -*-
"""
    picbed-video
    ~~~~~~~~~~~~

    Upload video to picbed.

    :copyright: (c) 2020 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

__version__ = '0.1.2'
__author__ = 'staugur <staugur@saintic.com>'
__hookname__ = 'picbed-video'
__description__ = '上传视频'
__appversion__ = '1.8.0'

import json
from functools import partial
from random import choice
from os.path import splitext
from posixpath import join
from redis import RedisError
from werkzeug.utils import secure_filename
from flask import render_template, request, g, current_app, url_for
from utils.web import apilogin_required, login_required
from utils.tool import allowed_file, get_current_timestamp, parse_valid_comma,\
    sha256, rsp, is_all_fail, get_today, generate_random, list_equal_split

intpl_nav = 'upvideo/nav.html'
UPLOAD_FOLDER = "upload"


@login_required
def route():
    return render_template('upvideo/index.html')


@apilogin_required
def upload():
    #: 视频上传接口，上传流程：
    #: 1. 必须登录，通过固定的picbed字段获取上传内容
    #: 2. 生成sha，文件名规则是年月日时分秒原名，上传到用户目录下
    #: 3. 保存到后端，存储数据返回响应
    res = dict(code=1, msg=None)
    if not g.signin:
        res.update(code=403, msg="Anonymous user is not sign in")
        return res
    if g.userinfo.status != 1:
        msg = (
            "Pending review, cannot upload pictures" if
            g.userinfo.status in (-2, -1) else
            "The user is disabled, no operation"
        )
        res.update(code=403, msg=msg)
        return res
    allowed_suffix = partial(
        allowed_file,
        suffix=("mp4", "ogg", "ogv", "webm", "3gp", "mov")
    )
    fp = request.files.get("picbed")
    title = request.form.get("title") or ""
    if not fp or not allowed_suffix(fp.filename):
        res.update(msg="No file or image format error")
        return res
    suffix = splitext(fp.filename)[-1]
    filename = secure_filename(fp.filename)
    if "." not in filename:
        filename = "%s%s" % (generate_random(8), suffix)
    stream = fp.stream.read()
    upload_path = join(g.userinfo.username, get_today("%Y/%m/%d"))
    sha = "sha256.%s.%s" % (get_current_timestamp(True), sha256(filename))
    includes = parse_valid_comma(g.cfg.upload_includes or 'up2local')
    if len(includes) > 1:
        includes = [choice(includes)]
    data = current_app.extensions["hookmanager"].call(
        _funcname="upimg_save",
        _include=includes,
        _kwargs=dict(
            filename=filename,
            stream=stream,
            upload_path=upload_path,
            local_basedir=join(
                current_app.root_path,
                current_app.static_folder,
                UPLOAD_FOLDER
            )
        )
    )
    for i, result in enumerate(data):
        if result["sender"] == "up2local":
            data.pop(i)
            result["src"] = url_for(
                "static",
                filename=join(UPLOAD_FOLDER, upload_path, filename),
                _external=True
            )
            data.insert(i, result)
    #: 判定后端存储全部失败时，上传失败
    if not data:
        res.update(code=1, msg="No valid backend storage service")
        return res
    if is_all_fail(data):
        res.update(
            code=1,
            msg="All backend storage services failed to save pictures",
        )
        return res
    #: 存储数据
    defaultSrc = data[0]["src"]
    pipe = g.rc.pipeline()
    pipe.sadd(rsp("index", "video", g.userinfo.username), sha)
    pipe.hmset(rsp("video", sha), dict(
        sha=sha,
        user=g.userinfo.username,
        title=title,
        filename=filename,
        upload_path=upload_path,
        ctime=get_current_timestamp(),
        src=defaultSrc,
        sender=data[0]["sender"],
        senders=json.dumps(data),
    ))
    try:
        pipe.execute()
    except RedisError:
        res.update(code=3, msg="Program data storage service error")
    else:
        res.update(
            code=0,
            sender=data[0]["sender"],
            src=defaultSrc,
        )
    return res


@apilogin_required
def remove():
    res = dict(code=1, msg=None)
    if not g.signin:
        res.update(code=403, msg="Anonymous user is not sign in")
        return res
    sha = request.form.get("sha")
    ivs = rsp("index", "video", g.userinfo.username)
    if not sha or not g.rc.sismember(ivs, sha):
        res.update(code=404, msg="Not Found")
        return res
    info = g.rc.hgetall(rsp("video", sha))
    if g.userinfo.username == info.get("user"):
        pipe = g.rc.pipeline()
        pipe.srem(ivs, sha)
        pipe.delete(rsp("video", sha))
        try:
            pipe.execute()
        except RedisError:
            res.update(msg="Program data storage service error")
        else:
            res.update(code=0)
            try:
                senders = json.loads(info.get("senders"))
                for i in senders:
                    current_app.extensions["hookmanager"].proxy(
                        i["sender"]
                    ).upimg_delete(
                        sha=sha,
                        upload_path=info["upload_path"],
                        filename=info["filename"],
                        basedir=(join(
                            current_app.root_path,
                            current_app.static_folder,
                            UPLOAD_FOLDER
                        ) if i["sender"] == "up2local"
                            else i.get("basedir")),
                        save_result=i
                    )
            except (ValueError, AttributeError, Exception):
                pass
    else:
        res.update(code=403, msg="Forbidden")
    return res


@apilogin_required
def waterfall():
    res = dict(code=1, msg=None)
    if not g.signin:
        res.update(code=403, msg="Anonymous user is not sign in")
        return res
    #: 依次根据ctime、filename排序
    sort = request.args.get("sort") or request.form.get("sort") or "desc"
    #: 符合人类习惯的page，第一页是1（程序计算需要减1）
    page = request.args.get("page") or request.form.get("page") or 1
    #: 返回数据条数
    limit = request.args.get("limit") or request.form.get("limit") or 10
    try:
        page = int(page) - 1
        limit = int(limit)
        if page < 0:
            raise ValueError
    except (ValueError, TypeError):
        res.update(code=2, msg="Parameter error")
        return res

    vs = g.rc.smembers(rsp("index", "video", g.userinfo.username))
    pipe = g.rc.pipeline()
    for sha in vs:
        pipe.hgetall(rsp("video", sha))
    try:
        result = pipe.execute()
    except RedisError:
        res.update(code=3, msg="Program data storage service error")
    else:
        data = []
        if result and isinstance(result, (tuple, list)):
            for i in result:
                i.update(
                    senders=json.loads(i["senders"]),
                    ctime=int(i["ctime"]),
                )
                data.append(i)
        data = sorted(
            data,
            key=lambda k: (k.get('ctime', 0), k.get('filename', '')),
            reverse=False if sort == "asc" else True
        )
        count = len(data)
        data = list_equal_split(data, limit)
        pageCount = len(data)
        if page < pageCount:
            res.update(
                code=0,
                count=count,
                data=data[page],
                pageCount=pageCount,
            )
        else:
            res.update(code=3, msg="No data")
    return res
