from .entities import Item
from inventorybot.utils import is_numeric


class ItemCreator:
    def __init__(self):
        self.item: Item = None
        self.state = "name"

    def get_messages(self) -> list[str]:
        if self.state == "name":
            return ["Qual o nome?"]

        if self.state == "quantity":
            return ["Qual a quantidade?"]

        if self.state == "main":
            return ["Item atual:", str(self.item), "Opções:"]

        return []

    def handle_message(self, message_text) -> bool:
        if self.state == "name":
            self.item = Item(name=message_text)
            self.state = "quantity"
            return True

        if self.state == "quantity":
            if message_text.isdigit():
                self.item.quantity = int(message_text)
                self.state = "main"
                return True
            else:
                return False

        return False

    def get_options(self):
        if self.state == "main":
            return [["Alterar quantidade", "set_quantity"], ["Cancelar", "cancel"]]

        return []


class Orchestrator:
    def __init__(self):
        self.item_creator = None

    def new_item(self):
        self.item_creator = ItemCreator()

    def get_messages(self):
        if self.item_creator:
            return self.item_creator.get_messages()
        else:
            return []

    def get_options(self):
        if self.item_creator:
            return self.item_creator.get_options()
        else:
            return [["Criar novo item", "new_item"]]

    def handle_message(self, message_text) -> bool:
        if self.item_creator:
            return self.item_creator.handle_message(message_text)
        else:
            return False
