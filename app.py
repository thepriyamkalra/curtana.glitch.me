# For curtana.surge.sh
# By Priyam Kalra

from shutil import rmtree
from datetime import date
from time import sleep
from production import Config
from markdown import markdown
from subprocess import check_output
from os import rename, listdir, remove, path
from jinja2 import Environment, FileSystemLoader


# Event handler
async def handler(event):
    data = {}
    messages = []
    today = date.today().strftime("%B %d, %Y")
    chats = Config.CHATS
    log([today + " -- its update day!", "Updates chat(s): " + str(chats)])
    for chat in chats:
        async for message in client.iter_messages(chat):
            messages.append(message)
    for message in messages:
        text = message.text if message.text is not None else ""
        if (True if "#ROM" in text else (True if "#Port" in text else (True if "#Kernel" in text else (True if "#Recovery" in text else False)))):
            title = f"{text.split()[0][1:]}"
            if title not in Config.BLOCKED_UPDATES:
                with open("surge/index.html", "r") as index:
                    with open("index.bak", "w") as backup:
                        backup.write(index.read())
                if title.lower() not in str(data.keys()).lower():
                    data.update({title: text})
                    image = await client.download_media(message, f"surge/{title}/")
                    thumbnail = f"surge/{title}/thumbnail.png"
                    rename(image, thumbnail)
                    parse_template(title=title, text=parse_text(
                        data[title][len(title)+1:]))
    parsed_data = parse_data(data)
    parse_template(title="404.html")
    parse_template(title="index.html", roms=sorted(parsed_data[0]), kernels=sorted(parsed_data[1]), recoveries=sorted(
        parsed_data[2]), latest=[parsed_data[0][0], parsed_data[1][0], parsed_data[2][0]], today=today)
    log("Update completed.")
    to_backup = {"surge/base.html": "base.html",
                 "surge/template.html": "template.html"}
    rename_files(to_backup)
    deploy()
    log("Cleaning up leftover files..")
    for f in listdir("surge"):
        if path.isdir(f"surge/{f}"):
            rmtree(f"surge/{f}")
    remove("surge/index.html")
    to_restore = {"base.html": "surge/base.html",
                  "template.html": "surge/template.html", "index.bak": "surge/index.html"}
    rename_files(to_restore)
    log(["Cleaned up all leftover files.", "All jobs executed, idling.."])

# Helpers
def parse_text(text):
    changes = {"**": "", "__": "", "~~": "", "`": "", "▪️": "• ", "\n": "\n<br>"}
    terms = text.split()
    for term in terms:
        if term.startswith("@"):
            changes.update({term: f"[{term}](https://t.me/{term[1:]})"})
    for a, b in changes.items():
        text = text.replace(a, b)
    text = markdown(text)
    return text


def parse_data(data):
    roms = []
    kernels = []
    recoveries = []
    for title, value in data.items():
        if "#ROM" in value:
            roms.append(title)
        if "#Port" in value:
            roms.append(title)
        if "#Kernel" in value:
            kernels.append(title)
        if "#Recovery" in value:
            recoveries.append(title)
    return [roms, kernels, recoveries]


def parse_template(title, **kwargs):
    path = f"surge/{title}/index.html"
    if title.endswith(".html"):
        path = f"surge/{title}"
        jinja2_template = str(open(path, "r").read())
    else:
        kwargs["title"] = title
        jinja2_template = str(open("surge/template.html", "r").read())
    template_object = Environment(
        loader=FileSystemLoader("surge")).from_string(jinja2_template)
    static_template = template_object.render(**kwargs)
    with open(path, "w") as f:
        f.write(static_template)


def log(text):
    if type(text) is not list:
        text = [text]
    for item in text:
        logger.info(item)
        sleep(1)


def rename_files(file_dict):
    for src, dst in file_dict.items():
        rename(src, dst)


def deploy():
    log(f"Deploying {Config.SUBDOMAIN}.surge.sh..")
    output = check_output(
        f"surge surge https://{Config.SUBDOMAIN}.surge.sh", shell=True)
    if "Success!" in str(output):
        log(f"{Config.SUBDOMAIN}.surge.sh deployed sucessfully.")
    else:
        log(f"Failed to deploy {Config.SUBDOMAIN}.surge.sh " +
            "\nError: " + str(output))


async def authorize(event):
    chat = await event.get_chat()
    tag = f"@{chat.username}"
    if tag in Config.CHATS:
        log(f"Authorized chat: {tag}")
        return True
    return False

# Event Dispatchers
@client.on(register(outgoing=True, func=authorize))
async def manual(event):
    log("Starting jobs for manual update.")
    await handler(event)


@client.on(register(incoming=True, func=authorize))
async def automatic(event):
    log("Starting jobs for automatic update.")
    await handler(event)
