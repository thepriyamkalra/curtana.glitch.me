# For curtana.glitch.me // curtana.surge.sh // curtana.herokuapp.com
# By justaprudev

import json
import shutil
import datetime
from pathlib import Path
from telethon.extensions import html
from git import Repo, Actor, GitCommandError
from jinja2 import Environment, FileSystemLoader

NAME = Path(__file__).stem
DEFAULT_DATA = {
    "chats": ["@username"],
    "item_types": ["rom", "kernel", "recovery"],
    "blocked_items": [],
    "filters": [NAME],
    "git": None,
}
DATA = db.get(NAME) or db.add(name=NAME, value=DEFAULT_DATA)
CWD = Path(DATA["git"].split("/")[-1])
GLITCH_FOLDER = Path(__file__).parent / "glitch"
DOMAIN = f"{CWD}.glitch.me"
DATE = datetime.date.today().strftime("%B %d, %Y")


@polygon.on(
    incoming=True,
    func=lambda e: f"@{e.chat.username}" in DATA["chats"] if e.chat else False,
)
@polygon.on(command=NAME)
async def glitch(e):
    if e.sender.username == polygon.user.username:
        await e.delete()
    if not DATA:
        polygon.log(f"Initialization required to use {NAME} pack.")
        return
    polygon.log(
        f"{DATE} -- its update day!"
        + f"\nUpdates chat(s): {DATA['chats']}"
        + f"\nEvent chat: @{e.sender.username}"
    )
    if CWD.exists():
        shutil.rmtree(CWD)
    glitch_repository = clone_from_glitch(DATA["git"])
    titles = {key: [] for key in DATA["item_types"]}
    for i in titles:
        Path.mkdir(CWD / i, exist_ok=True)
    for chat in DATA["chats"]:
        async for msg in polygon.iter_messages(chat):
            content = msg.message or "#"
            title = content.split()[0][1:]
            lower_content, lower_title = content.lower(), title.lower()
            if (
                not title
                or not is_required_content(lower_content)
                or lower_title in map(str.lower, DATA["blocked_items"])
            ):
                continue
            for content_type in titles:
                content_list = titles[content_type]
                if f"#{content_type}" in lower_content and lower_title not in map(
                    str.lower, content_list
                ):
                    content_list.append(title)
                    path = CWD / content_type / lower_title
                    path.mkdir(exist_ok=True)
                    banner = await get_banner(msg, path)
                    html_content = html.unparse(content, msg.entities)
                    write_webpage(
                        path=path,
                        title=title,
                        content=parse_content(html_content.replace(f"#{title}", "", 1)),
                        banner=banner,
                    )
    polygon.log(json.dumps(titles, sort_keys=True, indent=1))
    write_webpage(
        path=GLITCH_FOLDER / "index.html",
        roms=remove_duplicates(titles["rom"]),
        kernels=remove_duplicates(titles["kernel"]),
        recoveries=remove_duplicates(titles["recovery"]),
        get_random_color=get_random_color,
        len=len,
        date=DATE,
    )
    push_to_glitch(glitch_repository)
    polygon.log("Update completed.")


async def get_banner(msg, path: Path) -> str:
    # Declared twice for the sake of readability
    media = await polygon.download_media(msg, path)
    media = Path(media)
    path /= "banner" + media.suffix
    parents = list(map(lambda i: i.stem, path.parents))
    if media.suffix == ".mp4":
        banner = (
            "<video style='border-radius: 10px;' height=255 autoplay loop muted playsinline>"
            f"<source src='https://{DOMAIN}/{parents[1]}/{parents[0]}/{path.name}' type='video/mp4'>"
            "</video>"
        )
    else:
        path = path.with_suffix(".png")
        banner = f"<img src='https://{DOMAIN}/{parents[1]}/{parents[0]}/{path.name}' height='255'>"
    media.rename(path)
    return banner


def parse_content(content) -> str:
    replacements = {
        "<strong>": "",
        "</strong>": "",
        "<em>": "",
        "</em>": "",
        "\n": "\n                 <br>",
    }
    for i in content.split():
        if i.startswith("@"):
            replacements[i] = f"<a href=https://t.me/{i[1:]}>{i}</a>"
    for old, new in replacements.items():
        content = content.replace(old, new)
    return content


def write_webpage(path: Path, title=None, **variables) -> None:
    if title:
        path /= "index.html"
        variables["title"] = title
        jinja2_template = open(GLITCH_FOLDER / "template.html", "r").read()
    else:
        jinja2_template = open(path, "r").read()
        path = CWD / path.name
    template_object = Environment(loader=FileSystemLoader(GLITCH_FOLDER)).from_string(
        jinja2_template
    )
    with open(path, "w") as f:
        f.write(template_object.render(**variables))


def clone_from_glitch(git_url) -> Repo:
    repo = Repo.clone_from(git_url, CWD)
    try:
        repo.head.reset("HEAD~1", index=True, working_tree=True)
    except GitCommandError:
        polygon.log("clone: On root commit.")
    for i in Path(GLITCH_FOLDER).glob("*"):
        if i.is_dir():
            shutil.copytree(i, f"{CWD}/{i.stem}", dirs_exist_ok=True)
    return repo


def push_to_glitch(repo: Repo) -> None:
    actor = Actor(f"Glitch ({CWD})", "none")
    origin = repo.remote()
    index = repo.index
    index.add("*")
    commit = str(
        index.commit(
            # Glitch's signature commit message
            "Checkpoint 🚀",
            author=actor,
            committer=actor,
        )
    )
    push = origin.push(force=True)[0]
    polygon.log(
        f"{DOMAIN} deployed successfully!"
        if commit[:7] in push.summary
        else f"Error while deploying:\n{push.summary}\n{commit}"
    )


def is_required_content(content) -> bool:
    for i in DATA["filters"]:
        if f"#{i}" in content:
            return True
    return False


def get_random_color() -> str:
    from random import randint
    return f"hsl({randint(0, 359)}, 100%, 75%)"


def remove_duplicates(l: list) -> list:
    # This is the equivalent of list(set(l)) but it preserves the order of the list
    return list(dict.fromkeys(l))
