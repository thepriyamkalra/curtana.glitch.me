# For curtana.glitch.me // curtana.surge.sh // curtana.herokuapp.com
# By Priyam Kalra

from os import rename, path
from time import sleep
from random import choice
from git import Repo, Actor
from markdown import markdown
from datetime import date as Date
from shutil import rmtree, copytree
from jinja2 import Environment, FileSystemLoader


CWD = ENV.GLITCH_APP


async def main(e):
    data = {}
    date = Date.today().strftime("%B %d, %Y")
    log(date + " -- its update day!", "Updates chat(s): " +
        str(ENV.CHATS), "Event chat: " + f"@{e.sender.username}")
    gl = Repo.clone_from(ENV.GLITCH_GIT_URL, CWD)
    for chat in ENV.CHATS:
        async for msg in client.iter_messages(chat):
            text = msg.text or ""
            if not validate(text):
                continue
            title = text.split()[0][1:]
            if title in ENV.BLOCKED:
                continue
            if title.lower() not in str(data.keys()).lower():
                data.update({title: text})
                logo = await get_media(msg, title)
                parse_template(title=title, text=parse_text(
                    data[title][len(title)+1:]), logo=logo)
    parsed_data = parse_data(data)
    parse_template(title="index.html", roms=sorted(parsed_data[0][1:]), kernels=sorted(parsed_data[1][1:]), recoveries=sorted(
        parsed_data[2][1:]), latest=[parsed_data[0][1], parsed_data[1][1], parsed_data[2][1]], count=[parsed_data[0][0], parsed_data[1][0], parsed_data[2][0]], get_color=get_color, choice=choice, date=date)
    log("Update completed.")
    deploy(gl)
    log("Cleaning up leftover files..")
    rmtree(CWD)
    log("Cleaned up all leftover files.", "All jobs executed, idling..")


async def get_media(msg, title):
    media = await client.download_media(msg, f"{CWD}/{title}/")
    if media.endswith((".png", ".jpg", ".jpeg")):
        logo_path = f"{CWD}/{title}/logo.png"
        logo = f"<img src='https://curtana.glitch.me/{title}/logo.png' height='255'>"
    elif media.endswith((".mp4")):
        logo_path = f"{CWD}/{title}/logo.mp4"
        logo = f"<video style='border-radius: 10px;' height=255 autoplay loop muted playsinline><source src='https://curtana.glitch.me/{title}/logo.mp4' type='video/mp4'></video>"
    rename(media, logo_path)
    return logo


def parse_text(text):
    changes = {"**": "", "__": "", "~~": "",  "`": "",
               "▪️": "> ", "•": ">", "\n": "\n<br>"}
    words = text.split()
    for word in words:
        if word.startswith("@"):
            changes.update({word: f"[{word}](https://t.me/{word[1:]})"})
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
    path = f"{CWD}/{title}/index.html"
    to_path = None
    if title.endswith(".html"):
        path = f"glitch/{title}"
        to_path = f"{CWD}/{title}"
        jinja2_template = str(open(path, "r").read())
    else:
        kwargs["title"] = title
        jinja2_template = str(open("glitch/template.html", "r").read())
    template_object = Environment(
        loader=FileSystemLoader("glitch")).from_string(jinja2_template)
    static_template = template_object.render(**kwargs)
    with open(to_path or path, "w") as f:
        f.write(static_template)


def validate(text):
    for req in ENV.FILTERS:
        if f"#{req.lower()}" in text.lower():
            return True
    return False


async def auth(e):
    chat = await e.get_chat()
    try:
        if f"@{chat.username}" in ENV.CHATS:
            return True
    except:
        pass
    return False


def log(*text):
    for item in text:
        logger.info(item)
        if len(text) > 1:
            sleep(1)


def deploy(gl):
    if path.isdir(f"glitch/static"):
        copytree(f"glitch/static", f"{CWD}/static", dirs_exist_ok=True)
    actor = Actor(f"Glitch ({CWD})", "None")
    gl.index.add("*")
    gl.index.write()
    commit = gl.index.commit("Automatic deploy", author=actor, committer=actor)
    push = gl.remote().push()[0]
    if str(commit)[:7] in push.summary:
        log(f"{CWD}.glitch.me deployed successfully!")
    else:
        log("Error while deploying:\n" + push.summary,
            str(commit), str(commit)[:7])


def get_color():
    return f"hsl({choice(range(359))}, 100%, 75%)"


@client.on(events(outgoing=True, func=auth))
@client.on(events(incoming=True, func=auth))
async def run(e):
    await main(e)
