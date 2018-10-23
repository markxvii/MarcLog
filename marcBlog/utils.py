'''
工具类
'''

from urllib.parse import urlparse, urljoin
from flask import request, redirect, url_for


# 检测目标地址是否为安全地址
def is_safe_url(target):
    # 获取主机URL(安全)
    ref_url = urlparse(request.host_url)
    # 将目标地址转换为绝对URL（未知）
    test_url = urlparse(urljoin(request.host_url, target))
    # 检测未知URL的网络协议和两者的服务器地址确保未知URL安全且在程序内部。
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def redirect_back(default='blog.index', **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))
