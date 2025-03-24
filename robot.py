import os

import botpy
from botpy import logging
from botpy.ext.cog_yaml import read
from botpy.message import GroupMessage, DirectMessage
import re
from PIL import Image
import requests

from dotenv import load_dotenv

import jmcomic

load_dotenv(verbose=True)   # 机器人配置文件
# JmOption.default().to_file("./jmconfig.yml") # jmcomic 配置文件
jmoption = jmcomic.create_option_by_file("./jmconfig.yml")
_log = logging.get_logger()

def all2PDF(comic_path, pdfpath, pdfname):
    img_list = []
    # 扫描download子目录，查询download目录下某个子目录是否存在
    if os.path.exists(f"{comic_path}"):
        # 获取子目录列表，并按数字排序
        subdirs = os.listdir(f"{comic_path}")
        subdirs.sort(key=lambda x: int(x))
        for subdir in subdirs:
            # 获取子目录下的所有文件，并按数字排序
            files = os.listdir(f"{comic_path}/{subdir}")
            files.sort(key=lambda x: int(x.split(".")[0]))
            for file in files:
                img_list.append(f"{comic_path}/{subdir}/{file}")
    if len(img_list) == 0:
        return False
    
    # 使用img2pdf库逐步处理图片并写入PDF
    import img2pdf
    
    # 创建PDF文件路径
    pdf_file_path = os.path.join(pdfpath, pdfname)
    
    # 使用img2pdf直接将图片路径列表转换为PDF，避免全部加载到内存
    with open(pdf_file_path, "wb") as f:
        f.write(img2pdf.convert(img_list))
    
    return True


def upload_file(file_path):
    url = "https://api.dmhy.org/upload.php"
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url, files=files)
    return response.json()

class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    # 群聊@事件
    async def on_group_at_message_create(self, message: GroupMessage):
        openid = message.author.member_openid
        _log.info(f"robot {openid} on_ready!")
        msg = message.content.strip()
        if msg.startswith("/jm"):
            args = msg.split(" ")
            if len(args) != 2:
                await message.reply(content=f"机器人{self.robot.name}收到你的@消息了: 但是命令格式有问题哦！")
                return
            if re.match(r"^\d+", args[1]) is None:
                await message.reply(content=f"机器人{self.robot.name}收到你的@消息了: 但是命令格式有问题哦！")
                return
            # await message.reply(content=f"机器人{self.robot.name}收到你的@消息了: 开始下载漫画{args[1]}")
            jmcomic.download_album(args[1], jmoption)
            result = all2PDF(f"./download/{args[1]}", "./output", f"{args[1]}.pdf")
            if not result:
                await message.reply(content=f"机器人{self.robot.name}收到你的@消息了: 漫画pdf处理失败")
                return
            await message.reply(content=f"机器人{self.robot.name}收到你的@消息了: 漫画pdf处理成功", file_image=f"./output/{args[1]}.pdf")
        else:
            await message.reply(content=f"机器人{self.robot.name}收到你的@消息了: 但是目前不支持该功能哦！")

    

if __name__ == "__main__":
    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=os.getenv("appid"), secret=os.getenv("secret"))
