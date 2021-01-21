# For curtana.glitch.me // curtana.surge.sh // curtana.herokuapp.com
# By justaprudev

import json
import subprocess
import shutil
import asyncio
import requests
import datetime
from pathlib import Path
from telethon.extensions import html
from git import Repo, Actor, GitCommandError
from jinja2 import Environment, FileSystemLoader

NAME = Path(__file__).stem
DEFAULT_DATA = {
        "chats": ["@curtanacloud"],
        "item_types": ["rom", "kernel", "recovery", "port", "gsi"],
        "blocked_items": [],
        "filters": [],
        "git": None
        }
DATA = polygon.db.get(NAME) or polygon.db.add(name=NAME, value=DEFAULT_DATA) or DEFAULT_DATA
CWD = Path(DATA["git"].split("/")[-1])
GLITCH_FOLDER = Path(__file__).parent / "glitch"
DOMAIN = f"{CWD}.glitch.me"
DATE = datetime.date.today().strftime("%B %d, %Y")

@polygon.on(incoming=True, func=lambda e: f"@{e.chat.username}" in DATA["chats"] if e.chat else False)
@polygon.on(pattern=NAME)
async def curtana(e):
    if e.sender.username == polygon.user.username: await e.delete()
    polygon.log(
        f"{DATE} -- its update day!" +
        f"\nUpdates chat(s): {DATA['chats']}" + 
        f"\nEvent chat: @{e.sender.username}"
    )
    if CWD.exists(): shutil.rmtree(CWD)
    titles = {key : [] for key in DATA["item_types"]}
    glitch_repository = clone_from_glitch(DATA["git"])
    for chat in DATA["chats"]:
        async for msg in polygon.iter_messages(chat):
            content = msg.message or "#"
            title = content.split()[0][1:]
            lower_content, lower_title = content.lower(), title.lower()
            if not title or not is_required_content(lower_content) or lower_title in map(str.lower, DATA["blocked_items"]): continue
            for content_type in titles:
                content_list = titles[content_type]
                if f"#{content_type}" in lower_content and lower_title not in map(str.lower, content_list):
                    content_list.append(title)    
                    banner = await get_banner(msg, title)
                    html_content = html.unparse(content, msg.entities)
                    write_webpage(
                        title=title, 
                        content=parse_content(html_content.replace(f"#{title}", "", 1)), 
                        banner=banner
                        )
    polygon.log(json.dumps(titles, sort_keys=True, indent=1))
    write_webpage(
        title="index.html",
        roms=remove_duplicates(titles["rom"] + titles["port"] + titles["gsi"]),
        kernels=remove_duplicates(titles["kernel"]),
        recoveries=remove_duplicates(titles["recovery"]),
        get_random_color=get_random_color,
        len=len,
        date=DATE
    )
    push_to_glitch(glitch_repository)
    polygon.log("Update completed.")
    polygon.log(f"Waking up {DOMAIN}..")
    try: r = requests.head(f"http://{DOMAIN}")
    except requests.exceptions.ConnectionError: polygon.log(f"Couldn't establish a connection with {DOMAIN}")
    else: polygon.log(f"Done with {r}")


async def get_banner(msg, title):
    media = await polygon.download_media(msg, f"{CWD}/{title}/")
    if not media: return ""
    banner_path = f"{CWD}/{title}/banner"
    video_ext = ".mp4"
    if media.endswith(video_ext):
        banner_path += video_ext
        banner = f"<video style='border-radius: 10px;' height=255 autoplay loop muted playsinline><source src='https://{DOMAIN}/{title}/banner.mp4' type='video/mp4'></video>"
    else:
        banner_path += ".png"
        banner = f"<img src='https://{DOMAIN}/{title}/banner.png' height='255'>"
    Path(media).rename(banner_path)
    return banner

def parse_content(content):
    replacments = {
        "<strong>": "", "</strong>": "", "<em>": "",  "</em>": "",
        "\n": "\n<br>"
        }
    for i in content.split():
        if i.startswith("@"):
            replacments[i] = f"<a href=https://t.me/{i[1:]})>{i}</a>"
    for old, new in replacments.items():
        content = content.replace(old, new)
    return content

def write_webpage(title, **variables):
    path = f"{CWD}/{title}/index.html"
    to_path = None
    if title.endswith(".html"):
        path = GLITCH_FOLDER / title
        to_path = f"{CWD}/{title}"
        jinja2_template = str(open(path, "r").read())
    else:
        variables["title"] = title
        jinja2_template = str(open(GLITCH_FOLDER / "template.html", "r").read())
    template_object = Environment(
        loader=FileSystemLoader(GLITCH_FOLDER)
        ).from_string(jinja2_template)
    with open(to_path or path, "w") as f:
        f.write(template_object.render(**variables)) 

def clone_from_glitch(repo):
    repo = Repo.clone_from(DATA["git"], CWD)
    try: repo.head.reset("HEAD~1", index=True, working_tree=True)
    except GitCommandError: pass
    for i in Path(GLITCH_FOLDER).glob("*"):
        if i.is_dir(): shutil.copytree(i, f"{CWD}/{i.stem}", dirs_exist_ok=True)
    return repo

def push_to_glitch(repo: Repo):
    actor = Actor(f"Glitch ({CWD})", "none")
    origin = repo.remote()
    index = repo.index
    index.add("*")
    files = set(map(lambda i: i.split("/")[0], repo.git.diff("HEAD", name_only=True, diff_filter="A").splitlines()))
    if "index.html" in files: files.remove("index.html")
    commit = str(index.commit(f"Added {files}", author=actor, committer=actor, parent_commits=None))
    push = origin.push(force=True)[0]
    polygon.log(f"{DOMAIN} deployed successfully!" if commit[:7] in push.summary else f"Error while deploying:\n{push.summary}\n{commit}")

def is_required_content(content):
    for i in DATA["filters"]:
        if f"#{i}" in content:
            return True

def get_random_color():
    from random import randint
    return f"hsl({randint(0, 359)}, 100%, 75%)"

def remove_duplicates(l: list):
    # This is the equivalent of list(set(l)) but it preserves the order of the list
    return list(dict.fromkeys(l))
