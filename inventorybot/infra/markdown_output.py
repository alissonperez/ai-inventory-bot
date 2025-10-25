import os
from datetime import datetime
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from inventorybot.entities import Item, Box


def _dump_properties(properties):
    content = []
    properties_yaml = dump(properties, Dumper=Dumper)

    content.append(f"---")
    content.append(properties_yaml)
    content.append(f"---")

    return content


class MarkdownOutput:
    def __init__(self, filepath):
        self.filepath = filepath

    async def save(self, item: Item) -> Item:
        item.validate()

        item_filename = item.filename()

        item_dir = os.path.join(self.filepath, "Itens")
        os.makedirs(item_dir, exist_ok=True)

        full_path = f"{os.path.join(item_dir, item_filename)}.md"
        cover_filepath = self._cover(item, item_filename)
        if cover_filepath:
            item.photo = cover_filepath

        content = self._content(item)

        with open(full_path, "w") as file:
            file.write(content)

        self._ensure_box(item.box)

        return item

    def _content(self, item: Item):
        # File obsidian properties in yaml
        properties = item.to_dict()
        properties["created"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Replace photo by cover
        if item.photo:
            properties["cover"] = f"[[{item.cover_filename()}]]"
            del properties["photo"]

        if item.box:
            properties["box"] = f"[[{item.box.filename()}]]"
        if item.location:
            properties["location"] = f"[[{item.location}]]"

        content = _dump_properties(properties)
        content.append(f"# {item.name}")

        if item.description:
            content.append("")
            content.append("## Descrição")
            content.append("")
            content.append(f"{item.description}")

        if item.photo:
            content.append("")
            content.append(f"![[{item.cover_filename()}]]")

        return "\n".join(content)

    def _cover(
        self,
        item: Item,
        item_filename: str,
    ) -> str | None:
        if not item.photo:
            return None

        cover_filename = f"{item_filename}.jpg"
        cover_dir = os.path.join(self.filepath, "Itens", "attachments")
        os.makedirs(cover_dir, exist_ok=True)

        cover_filepath = os.path.join(cover_dir, cover_filename)

        print("Moving", item.photo, "to", cover_filepath)

        # move photo filename to attachments folder
        os.rename(item.photo, cover_filepath)

        return cover_filepath

    def _ensure_box(self, box: Box):
        if not box:
            return

        filename = box.filename()
        box_filename = f"{filename}.md"
        box_dir = os.path.join(self.filepath, "Caixas")
        os.makedirs(box_dir, exist_ok=True)

        box_filepath = os.path.join(box_dir, box_filename)

        # if file exists, do nothing
        if os.path.exists(box_filepath):
            return

        properties = box.to_dict()
        if "filename" in properties:
            del properties["filename"]

        content = _dump_properties(properties)
        content.append(f"# {box.name}")

        with open(box_filepath, "w") as file:
            file.write("\n".join(content))
