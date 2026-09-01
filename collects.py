import requests
import re
import os
import ipaddress
import random
import uuid
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

myID = uuid

# ✅ URL源与简称
sources = {
    # IPv4源
    'https://vps789.com/openApi/cfIpApi': 'VPS789',  # 每小时刷新一次
    # 'https://cf.090227.xyz/cmcc?ips=8': 'CM优选移动',
    # 'https://cf.090227.xyz/ct?ips=6': 'CM优选电信',
    # 'https://cf.090227.xyz/cu': 'CM联通优选',
    # 'https://www.wetest.vip/page/cloudflare/address_v4.html': 'WeTest',
    # 'https://ipdb.api.030101.xyz/?type=bestcf': 'IPDB'

    # IPv6源
    'https://www.wetest.vip/page/cloudflare/address_v6.html': 'WeTestV6',
    # 'https://ipdb.api.030101.xyz/?type=bestcfv6': 'IPDBv6',

}

PORT = '443'  # 目标端口号

# 正则表达式
ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
ipv6_candidate_pattern = r'([a-fA-F0-9:]{2,39})'

headers = {
    'User-Agent': 'Mozilla/5.0'
}

# 删除旧文件
for file in ['ipv4.txt', 'ipv6.txt', 'ipv4+6.txt', 'ym.txt']:
    if os.path.exists(file):
        os.remove(file)

# IP 存储
# 使用 list，不去重，API 返回多少条就保存多少条
ipv4_list = []
ipv6_list = []

# 当前时间
# utctimestamp = datetime.now().strftime('%Y%m%d%H%M')
# beijing_time = datetime.utcnow() + timedelta(hours=8)
# now_str = beijing_time.strftime('%Y-%m-%d_%H:%M')
# timestamp = beijing_time.strftime('%Y%m%d_%H:%M')


# 遍历来源
for url, shortname in sources.items():
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.text

        # ==========================================================
        # VPS789 API：直接按照 JSON 解析
        # ==========================================================
        if url == 'https://vps789.com/openApi/cfIpApi':

            api_data = response.json()

            # 获取 data
            data = api_data.get('data', {})

            # API分类 → 中文名称
            category_names = {
                'CT': '电信',
                'CU': '联通',
                'CM': '移动',
                'AllAvg': '综合'
            }

            # 按照 API 中的分类分别读取
            for category in ['CT', 'CU', 'CM', 'AllAvg']:

                ip_list = data.get(category, [])

                # 获取中文分类名称
                category_name = category_names.get(category, category)

                # API 返回多少条，就读取多少条
                for item in ip_list:

                    ip = item.get('ip')

                    if not ip:
                        continue

                    try:
                        # 确认是 IPv4
                        if ipaddress.ip_address(ip).version == 4:

                            ip_with_port = f"{ip}:{PORT}"

                            # 中文分类 + 随机字符串
                            comment = (
                                f"{category_name}-"
                                f"{myID.uuid4().hex[27:]}"
                                f"{str(random.randint(0, 10))}"
                            )

                            # 不去重，直接追加
                            ipv4_list.append(
                                f"{ip_with_port}#{comment}"
                            )

                    except ValueError:
                        continue

        # ==========================================================
        # 其他来源：保持原来的网页解析方式
        # ==========================================================
        else:

            if url.endswith('.txt'):
                text = content
            else:
                soup = BeautifulSoup(content, 'html.parser')
                elements = soup.find_all('tr') or soup.find_all('li') or soup
                text = '\n'.join(el.get_text() for el in elements)

            # ------------------------------------------------------
            # IPv4 提取
            # ------------------------------------------------------
            for ip in re.findall(ipv4_pattern, text):
                try:
                    if ipaddress.ip_address(ip).version == 4:

                        ip_with_port = f"{ip}:{PORT}"

                        comment = (
                            f"{shortname}-"
                            f"{myID.uuid4().hex[27:]}"
                            f"{str(random.randint(0, 10))}"
                        )

                        ipv4_list.append(
                            f"{ip_with_port}#{comment}"
                        )

                except ValueError:
                    continue

            # ------------------------------------------------------
            # IPv6 提取
            # ------------------------------------------------------
            for ip in re.findall(ipv6_candidate_pattern, text):
                try:

                    ip_obj = ipaddress.ip_address(ip)

                    if ip_obj.version == 6:

                        ip_with_port = f"[{ip_obj.compressed}]:{PORT}"

                        comment = (
                            f"{shortname}-"
                            f"{myID.uuid4().hex[27:]}"
                            f"{str(random.randint(0, 10))}"
                        )

                        ipv6_list.append(
                            f"{ip_with_port}#{comment}"
                        )

                except ValueError:
                    continue

    except requests.RequestException as e:
        print(f"[请求错误] {url} -> {e}")

    except Exception as e:
        print(f"[解析错误] {url} -> {e}")


# ==============================================================
# 写入 ipv4.txt（仅IPv4）
# ==============================================================

with open('ipv4.txt', 'w') as f4:

    for line in ipv4_list:
        f4.write(line + '\n')


# ==============================================================
# 写入 ipv6.txt（仅IPv6）
# ==============================================================

with open('ipv6.txt', 'w') as f6:

    for line in ipv6_list:
        f6.write(line + '\n')


# ==============================================================
# 写入 ipv4+6.txt（IPv4 + IPv6）
# ==============================================================

with open('ipv4+6.txt', 'w') as f46:

    for line in ipv4_list:
        f46.write(line + '\n')

    for line in ipv6_list:
        f46.write(line + '\n')


# ==============================================================
# 优选域名
# 获取 VPS789 Top20 域名 每天凌晨刷新
# ==============================================================

ym_dict = {}

ym_url = 'https://vps789.com/openApi/cfIpTop20'

try:

    response = requests.get(
        ym_url,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    # 解析 JSON
    api_data = response.json()

    # 获取 data.good
    good_list = api_data.get('data', {}).get('good', [])

    # 按 API 返回顺序读取 Top20
    for item in good_list:

        domain = item.get('ip')

        if domain:

            domain_with_port = f"{domain}:{PORT}"

            comment = (
                f"VPS789-"
                f"{myID.uuid4().hex[27:]}"
                f"{str(random.randint(0, 10))}"
            )

            ym_dict[domain_with_port] = comment


except requests.RequestException as e:
    print(f"[请求错误] {ym_url} -> {e}")

except Exception as e:
    print(f"[解析错误] {ym_url} -> {e}")


# ==============================================================
# 写入 ym.txt
# ==============================================================

with open('ym.txt', 'w') as fym:

    for domain in ym_dict:
        fym.write(
            f"{domain}#{ym_dict[domain]}\n"
        )


# ==============================================================
# 输出统计
# ==============================================================

print(
    f"✅ 域名写入 ym.txt，共 {len(ym_dict)} 个"
)

print(
    f"✅ IPv4 写入 ipv4.txt，共 {len(ipv4_list)} 个"
)

print(
    f"✅ IPv6 写入 ipv6.txt，共 {len(ipv6_list)} 个"
)

print(
    f"✅ IPv4 + IPv6 写入 ipv4+6.txt，共 "
    f"{len(ipv4_list) + len(ipv6_list)} 个"
)
