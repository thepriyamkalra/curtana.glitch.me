# For curtana.glitch.me
# By Priyam Kalra

from time import sleep
from random import choice
from shutil import rmtree
from markdown import markdown
from production import Config
from datetime import date as datetime
from subprocess import run, DEVNULL
from os import rename, listdir, remove, path
from jinja2 import Environment, FileSystemLoader


# Checks chat username
async def chat(e):
    chat = await e.get_chat()
    if f"@{chat.username}" in Config.CHATS:
        return True
    return False


# Event Dispatchers
@client.on(register(outgoing=True, func=chat))
async def manual(event):
    log("Starting jobs for manual update.")
    await handler(event)


@client.on(register(incoming=True, func=chat))
async def automatic(event):
    log("Starting jobs for automatic update.")
    await handler(event)


# Event handler
async def handler(event):
    data = {}
    messages = []
    date = datetime.today().strftime("%B %d, %Y")
    chats = Config.CHATS
    log([date + " -- its update day!", "Updates chat(s): " +
         str(chats), "Event chat: " + f"@{event.sender.username}"])
    for chat in chats:
        async for message in client.iter_messages(chat):
            messages.append(message)
    for message in messages:
        text = message.text if message.text is not None else ""
        if (True if "#Curtana" in text else(True if "#curtana" in text else False)):
            title = f"{text.split()[0][1:]}"
            if title not in Config.BLOCKED_UPDATES:
                with open("glitch/index.html", "r") as index:
                    with open("index.bak", "w") as backup:
                        backup.write(index.read())
                if title.lower() not in str(data.keys()).lower():
                    data.update({title: text})
                    media = await client.download_media(message, f"glitch/{title}/")
                    if media.endswith((".png", ".jpg", ".jpeg")):
                        logo = f"glitch/{title}/logo.png"
                        logo_html = f"<img src='https://curtana.glitch.me/{title}/logo.png' height='255'>"
                    elif media.endswith((".mp4")):
                        logo = f"glitch/{title}/logo.mp4"
                        logo_html = f"<video style='border-radius: 10px;' height=255 autoplay loop muted playsinline><source src='https://curtana.glitch.me/{title}/logo.mp4' type='video/mp4'></video>"
                    rename(media, logo)
                    parse_template(title=title, text=parse_text(
                        data[title][len(title)+1:]), logo=logo_html)
    parsed_data = parse_data(data)
    parse_template(title="index.html", roms=sorted(parsed_data[0][1:]), kernels=sorted(parsed_data[1][1:]), recoveries=sorted(
        parsed_data[2][1:]), latest=[parsed_data[0][1], parsed_data[1][1], parsed_data[2][1]], count=[parsed_data[0][0], parsed_data[1][0], parsed_data[2][0]], random_pastel=random_pastel, choice=choice, date=date)
    log("Update completed.")
    deploy()
    log("Cleaning up leftover files..")
    for f in listdir("glitch"):
        if path.isdir(f"glitch/{f}"):
            if f != "static":
                rmtree(f"glitch/{f}")
    rmtree(Config.GLITCH_APP)
    remove("glitch/index.html")
    rename("index.bak", "glitch/index.html")
    log(["Cleaned up all leftover files.", "All jobs executed, idling.."])


# Helpers
def parse_text(text):
    changes = {"**": "", "__": "", "~~": "",  "`": "",
               "▪️": "> ", "•": ">", "\n": "\n<br>"}
    terms = text.split()
    for term in terms:
        if term.startswith("@"):
            changes.update({term: f"[{term}](https://t.me/{term[1:]})"})
    for a, b in changes.items():
        text = text.replace(a, b)
    text = markdown(text)
    return text


def parse_data(data):
    roms = [0]
    kernels = [0]
    recoveries = [0]
    for title, value in data.items():
        value = value.lower()
        if "#rom" in value:
            roms.append(title)
            roms[0] += 1
        elif "#port" in value:
            roms.append(title)
            roms[0] += 1
        elif "#kernel" in value:
            kernels.append(title)
            kernels[0] += 1
        elif "#recovery" in value:
            recoveries.append(title)
            recoveries[0] += 1
    return [roms, kernels, recoveries]


def parse_template(title, **kwargs):
    path = f"glitch/{title}/index.html"
    if title.endswith(".html"):
        path = f"glitch/{title}"
        jinja2_template = str(open(path, "r").read())
    else:
        kwargs["title"] = title
        jinja2_template = str(open("glitch/template.html", "r").read())
    template_object = Environment(
        loader=FileSystemLoader("glitch")).from_string(jinja2_template)
    static_template = template_object.render(**kwargs)
    with open(path, "w") as f:
        f.write(static_template)


def log(text):
    if type(text) is not list:
        text = [text]
    for item in text:
        logger.info(item)
        sleep(1)


def random_pastel():
    return f"hsl({choice(range(359))}, 100%, 75%)"


def deploy():
    log(f"Deploying {Config.GLITCH_APP}.glitch.me..")
    cmd = f"git config --global user.email 'none' && git config --global user.name 'Glitch ({Config.GLITCH_APP})' && git clone {Config.GLITCH_GIT_URL} && cd {Config.GLITCH_APP} && git reset HEAD~1 --hard && cp -r ../glitch/* ./ && rm base.html && rm template.html && git add . && git commit -am 'Automatic deploy' && git push --force"
    with open("output.log", "w") as out:
        run(cmd, stderr=out, stdout=out, shell=True)
    with open("output.log", "r") as out:
        output = out.read()
    if "master -> master" in str(output):
        log(f"{Config.GLITCH_APP}.glitch.me deployed successfully!")
    else:
        log("Error while deploying:\n" + str(output))
    remove("output.log")
