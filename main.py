import requests
import config
import time
import json
import os
import async_download as ad
import asyncio
import tools


# 组装搜索关键词和调用api的参数
def makeup_keywords_to_check(
    artist_name=config.ARTIST_NAME,
    sort_by=config.SORT_BY,
    desc=config.DESCENDING,
    rating=config.RATING,
    tags=config.SEARCH_TAGS,
    user_id=config.API["user_id"],
    api_key=config.API["api_key"],
):
    keywords = artist_name + ' ' + tags

    if sort_by:
        tags = f"sort:{sort_by}:{desc} " + keywords

    elif rating:
        tags = f"rating:{rating} " + keywords

    params = {"tags": tags, "user_id": user_id, "api_key": api_key, "json": 1}
    
    return params


# 获取搜索基本信息
def get_info(params: dict, url=config.API_URL, headers=config.HEADERS):
    tags = params["tags"]
    params["limit"] = 1

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


# 获取详细json数据
def get_details(params, url=config.API_URL, headers=config.HEADERS):
    params["json"] = 1

    try:
        print("正在获取详情数据...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(0.1)

        if response.status_code == 200:
            raw_data = json.loads(response.content)

            posts = []
            if isinstance(raw_data, dict):
                posts = raw_data.get("post", [])
            elif isinstance(raw_data, list):
                posts = raw_data
            
            return posts

        else:
            print(f"请求失败: {response.status_code}")
            return None

    except Exception as e:
        print(f"处理输入或请求时出错: {e}")
        return None


# 解析json 输出datalist
def parser(posts):
    data_list = []

    for post in posts:
        p_id = post.get("id")
        posted = post.get("created_at")
        uploader = post.get("owner")
        source = post.get("source", "")
        rating = post.get("rating")
        score = post.get("score")
        preview_url = post.get("preview_url")
        width = post.get("width")
        height = post.get("height")
        size_str = f"{width}x{height}"
        file_url = post.get("file_url") or post.get("sample_url") or post.get("preview_url")

        row = {
            "Id": p_id,
            "Posted": posted,
            "Uploader": uploader,
            "Rating": rating,
            "Score": score,
            "Size": size_str,
            "Source": source,
            "Preview": preview_url,
            "File_URL": file_url
        }

        data_list.append(row)

    return data_list


# 保存数据
def save_data(data_list, output_path=config.DATA_OUTPUT_PATH):
    import pandas as pd

    df = pd.DataFrame(data_list)
    df.drop(columns=["Source", "Preview"])
    df["Posted"] = pd.to_datetime(df["Posted"], format="%a %b %d %H:%M:%S %z %Y", utc=True).dt.strftime("%Y-%m-%d")
    columns_order = ["Id", "Posted", "Uploader", "Rating", "Score", "Size"]
    df = df.reindex(columns=columns_order)

    file_name = tools.output_name() + ".csv"
    output_path += rf"\{file_name}"

    if not os.path.exists(output_path):
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"已保存 {len(df)} 条数据到: {output_path}")
        return

    try:
        existing_ids = pd.read_csv(output_path, usecols=["Id"])["Id"].unique()
        df = df[~df["Id"].isin(existing_ids)]
        if not df.empty:
            df.to_csv(output_path, index=False, header=False, encoding="utf-8-sig", mode="a")
            print(f"新写入 {len(df)} 条数据到: {output_path}")

        else:
            print("没有新数据需要写入")

    except:
        print(f"保存失败 检查文件夹 {output_path} 下的同名文件 {file_name}")


if __name__ == "__main__":
    params = makeup_keywords_to_check()
    params = get_info(params)
    
    posts = get_details(params)
    data_list = parser(posts)
    
    if config.SAVE_DATA:
        save_data(data_list)
        
    if config.DOWNLOAD_IMAGES:
        import sys
        
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(ad.download_imgs_async(data_list))

# 交互界面测试代码
# response = makeup_keywords_to_check()
