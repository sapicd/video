picbed-video
=============

这是基于 `picbed <https://github.com/staugur/picbed>`_
的一个小的扩展模块，用来上传视频。

安装
------

- 正式版本

    `$ pip install -U picbed-video`

- 开发版本

    `$ pip install -U git+https://github.com/staugur/picbed-video.git@master`


开始使用
----------

此扩展请在部署 `picbed <https://github.com/staugur/picbed>`_ 图床后使用，需要
其管理员进行添加扩展、设置钩子等操作。

添加：
^^^^^^^^

请在 **站点管理-钩子扩展** 中添加第三方钩子，输入名称：upvideo，
确认后提交即可加载这个模块（请在服务器先手动安装或Web上安装第三方包）。

