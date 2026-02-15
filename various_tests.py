import requests
import config
import time
import json
import xml.etree.ElementTree as ET


def get_json_info(params: dict, url=config.API_URL, headers=config.HEADERS):
    tags = params["tags"]
    params["limit"] = 1
    params["json"] = 1

    try:
        print(f"正在查询关键词: {tags} ...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(0.1)

        if response.status_code == 200:
            data = json.loads(response.content)

            if "@attributes" in data and "count" in data["@attributes"]:
                count = int(data["@attributes"]["count"])
            else:
                # 如果没有 @attributes，通常说明没搜到结果或者 API 变动
                count = 0

            if count == 0:
                print("该关键词未匹配到图片。")
                return False

            print(f"关键词: '{tags}' 共找到 {count} 张图片。")

            imgnum = input("想要获取的图片数量是：")

            if imgnum == "all":
                params["limit"] = count
                return params

            elif imgnum == "0":
                return False

            while not imgnum.isdigit():
                print("请输入有效的数字。\n")
                imgnum = input("想要获取的图片信息数量是：")
            
            input_num = int(imgnum)
            params["limit"] = min(input_num, count)

            return params

        else:
            print(f"请求失败: {response.status_code}")

    except Exception as e:
        print(f"发生网络或其他错误: {e}")
        
        
# 获取搜索基本信息
def get_xml_info(params: dict, url=config.API_URL, headers=config.HEADERS):
    tags = params["tags"]
    params["limit"] = 0

    try:
        print(f"正在查询关键词: {tags} ...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(0.1)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
            count_str = root.get("count")
            if not count_str:
                count_str = root.attrib.get("count", "0")

            count = int(count_str)

            if count == 0:
                print("该关键词未匹配到图片。")
                return False

            print(f"关键词: '{tags}' 共找到 {count} 张图片。")

            imgnum = input("想要获取的图片数量是：")

            if imgnum == "all":
                params["limit"] = count
                return params

            elif imgnum == 0:
                return False

            while not imgnum.isdigit():
                print("请输入有效的数字。\n")
                imgnum = input("想要获取的图片信息数量是：")

            params["limit"] = int(imgnum)

            return params

        else:
            print(f"请求失败: {response.status_code}")

    except Exception as e:
        print(f"发生网络或其他错误: {e}")