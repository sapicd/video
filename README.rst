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

请在 **站点管理-钩子扩展** 中添加第三方钩子，输入模块名：upvideo，
确认后提交即可加载这个模块（请在服务器先手动安装或Web上安装第三方包）。

使用说明：
^^^^^^^^^^^^

针对已登录用户，不允许匿名，上传到默认存储中。

登录后，右侧菜单下拉有我的视频，允许上传mp4|ogg|ogv|webm|3gp|mov格式，
不超过10MB，支持删除。

ps：上传、删除效果同图片上传、删除，即如果钩子支持则会物理删除。

ps：上传按 **用户/年/月/日/原名** 保存，同一天同文件会覆盖。

ps：播放效果在不同浏览器下有所不同，甚至不能播放，推荐使用mp4格式！

