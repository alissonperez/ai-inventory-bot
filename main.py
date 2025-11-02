from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()  # take environment variables

from os import path
import tempfile
import re
import os
import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from icecream import ic

from slugify import slugify
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from inventorybot.settings import settings
from inventorybot.entities import Item, Status, Location
from inventorybot.infra.markdown_output import MarkdownOutput
from inventorybot.vision import VisionService
from inventorybot.parser import parser


# =========================
# Configuração
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = settings.telegram_token
OUTPUT_DIR = settings.output_dir
ALLOWED_USER_IDS = settings.allowed_user_ids

re_multiple_spaces = re.compile(r"\s+")

output = MarkdownOutput(OUTPUT_DIR)
vision_service = VisionService()

# ========================
# Decorators
# ========================


# decorator @filter_users
def filter_users(func):
    async def wrapper(update: Update, *args, **kwargs):
        if ALLOWED_USER_IDS and update.effective_user.id not in ALLOWED_USER_IDS:
            await update.message.reply_text(
                "Você não tem permissão para usar este bot."
            )
            return

        return await func(update, *args, **kwargs)

    return wrapper


# =========================
# Helpers
# =========================
def reset_context(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["item"] = Item(
        quantity=1,
        location=context.user_data.get("last_location"),
        tags=context.user_data.get("last_tags", []),
    )
    if "action" in context.user_data:
        del context.user_data["action"]


def ensure_item(context: ContextTypes.DEFAULT_TYPE) -> Item:
    item = context.user_data.get("item")
    if not isinstance(item, Item):
        reset_context(context)
        item = context.user_data["item"]

    return item


def handle_tags(text: str) -> list[str]:
    tags_text = re_multiple_spaces.sub(" ", text)
    tags_striped = [v.strip() for v in tags_text.split(",")]
    tags_with_no_space = [slugify(v) for v in tags_striped]
    return tags_with_no_space


def build_keyboard(item: Item) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🖊 Editar nome", callback_data="edit_nome"),
            InlineKeyboardButton(
                "📝 Editar descrição", callback_data="edit_description"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔢 Editar quantidade", callback_data="edit_quantidade"
            ),
        ],
        [InlineKeyboardButton("🖼 Editar foto", callback_data="edit_foto")],
        [
            InlineKeyboardButton(
                "📦 Editar localização", callback_data="edit_location"
            ),
        ],
        [
            InlineKeyboardButton("📏 Editar tamanho", callback_data="edit_size"),
            InlineKeyboardButton("❌ Remover", callback_data="remove_size"),
        ],
        [
            InlineKeyboardButton("🏷 Editar tags", callback_data="edit_tags"),
            InlineKeyboardButton("❌ Remover", callback_data="remove_tags"),
        ],
        [
            InlineKeyboardButton("💾 Gravar", callback_data="save_item"),
            InlineKeyboardButton(
                "💾 Gravar (novo contexto)", callback_data="save_item_new_context"
            ),
        ],
        [InlineKeyboardButton("❌ Descartar", callback_data="discard_item")],
    ]

    if item.photo:
        keyboard.insert(
            0,
            [
                InlineKeyboardButton(
                    "🤖 Extrair dados da imagem", callback_data="extract_vision_data"
                )
            ],
        )
    return InlineKeyboardMarkup(keyboard)


def render_summary(item: Item) -> str:
    status_txt = item.status.value if item.status else "-"
    description_txt = item.description or ""
    return (
        "📦 **Item atual:**\n\n"
        f"🧾 Nome: {item.name}\n"
        f"📝 Descrição: {description_txt}\n"
        f"📊 Quantidade: {item.quantity}\n"
        f"📏 Tamanho: {item.size}\n"
        f"📦 Localização: {item.location}\n"
        f"🏷️ Tags: {', '.join(item.tags) if item.tags else '*Nenhuma*'}\n"
        f"🔖 Status: {status_txt}"
    )


async def safe_edit_message(query, text: str):
    """Edita texto ou legenda conforme o tipo da mensagem que originou o callback."""
    try:
        if query.message.photo:
            await query.edit_message_caption(caption=text)
        else:
            await query.edit_message_text(text)
    except Exception as e:
        logger.exception("Erro ao editar mensagem: %s", e)


# =========================
# Handlers principais
# =========================


@filter_users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_context(context)
    await update.message.reply_text("Envie o nome ou a foto do item para começar.")


@filter_users
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = ensure_item(context)
    text = (update.message.text or "").strip()

    action = context.user_data.get("action", "edit_nome")

    # Se ainda não tem nome, define e pede quantidade
    if action == "edit_nome":
        try:
            item = handle_name(text, item)
        except ValueError:
            await update.message.reply_text("Nome inválido. Envie um nome válido.")
            return

        await show_summary(update, context)
        return

    # Se não tem quantidade, tenta converter
    if action == "edit_quantidade":
        try:
            item.quantity = int(text)
        except ValueError:
            await update.message.reply_text(
                "Quantidade inválida. Envie um número inteiro."
            )
            return
        await show_summary(update, context)
        return

    if action == "edit_description":
        item.description = text
        await show_summary(update, context)
        return

    # Se não tem tamanho, tenta converter
    if action == "edit_size":
        item.size = text
        await show_summary(update, context)
        return

    if action == "edit_location":
        item.location = Location(name=text)
        await show_summary(update, context)
        return

    if action == "edit_tags":
        item.tags = handle_tags(text)
        await show_summary(update, context)
        return

    # Se já tem nome e quantidade, apenas reexibe o resumo e opções
    await show_summary(update, context)


def convert_list_to_pairs(command_string):
    """
    # Convert string "c abc q 123"
    # to [[c abc], [q 123]]
    """

    # remove duplicated spaces
    command_string = command_string.strip()
    command_string = re_multiple_spaces.sub(" ", command_string)
    splited = command_string.split(" ")

    if len(splited) % 2 > 0:
        return None

    pairs = [splited[i : i + 2] for i in range(0, len(splited), 2)]
    return pairs


@filter_users
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = ensure_item(context)
    photo_caption = update.message.caption
    if photo_caption:
        try:
            item = handle_name(photo_caption, item)
        except ValueError as e:
            await update.message.reply_text(f"Erro ao processar legenda: {e}")
            return

    photo = update.message.photo[-1]
    filename = None

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filename = tmp.name

    file = await photo.get_file()
    print("saving at", filename)
    await file.download_to_drive(filename)
    item.photo = filename

    await show_summary(update, context)


def handle_name(name: str, item: Item) -> Item:
    item.name = name
    splited = name.strip().split(";")

    if len(splited) == 1:
        return item

    name, commands_str = splited[0], splited[1]
    commands = parser(commands_str)

    for command, *value in commands:
        value_str = " ".join(value)
        if command == "l":
            item.location = Location(name=value_str)
        elif command == "q":
            qtd = value_str
            if qtd.isdigit():
                item.quantity = int(qtd)
        elif command == "s":
            item.size = value_str
        elif command == "t":
            item.tags = handle_tags(value_str)

    item.name = name
    return item


async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = ensure_item(context)
    caption = render_summary(item)
    reply_markup = build_keyboard(item)

    # Se tem foto, envia como foto com legenda; senão, como texto
    if item.photo:
        await update.message.reply_photo(
            item.photo,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            caption,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )


# =========================
# Botões
# =========================


@filter_users
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    item = ensure_item(context)

    context.user_data["action"] = data

    if data == "edit_nome":
        await safe_edit_message(query, "Envie o nome:")
    elif data == "edit_description":
        await safe_edit_message(query, "Envie a descrição:")
    elif data == "edit_location":
        await safe_edit_message(query, "Informe o local:")
    elif data == "edit_quantidade":
        await safe_edit_message(query, "Envie a quantidade:")
    elif data == "edit_size":
        await safe_edit_message(query, "Informe o tamanho:")
    elif data == "edit_foto":
        await safe_edit_message(query, "Envie a foto:")
    elif data == "edit_tags":
        await safe_edit_message(query, "Envie as tags (separadas por ','):")
    elif data == "extract_vision_data":
        await extract_vision_data(query, context)
    elif data == "remove_size":
        item.size = None
        await safe_edit_message(query, "Tamanho removido.")
        await show_summary(query, context)
    elif data == "remove_tags":
        item.tags = []
        await safe_edit_message(query, "Tags removidas.")
        await show_summary(query, context)
    elif data == "save_item":
        _, success = await save(item, query)
        if success:
            context.user_data["last_location"] = item.location
            context.user_data["last_tags"] = item.tags
            reset_context(context)
        else:
            await show_summary(query, context)
    elif data == "save_item_new_context":
        _, success = await save(item, query)
        if success:
            context.user_data["last_location"] = None
            context.user_data["last_tags"] = None
            reset_context(context)
        else:
            await show_summary(query, context)
    elif data == "discard_item":
        reset_context(context)
        await safe_edit_message(query, "❌ Item descartado.")
    else:
        await safe_edit_message(query, "Ação não reconhecida.")


async def extract_vision_data(query, context: ContextTypes.DEFAULT_TYPE):
    item = ensure_item(context)
    if not item.photo:
        await safe_edit_message(query, "Nenhuma foto para analisar.")
        return

    if not vision_service:
        await safe_edit_message(
            query, "O serviço de visão não está configurado. Verifique a chave da API."
        )
        return

    try:
        await safe_edit_message(query, "🤖 Analisando imagem...")
        vision_result = vision_service.extract_item_details_from_image(item)
        item.name = vision_result.name
        item.description = vision_result.description

        caption = render_summary(item)
        reply_markup = build_keyboard(item)
        await query.edit_message_caption(
            caption=caption, reply_markup=reply_markup, parse_mode="Markdown"
        )

    except Exception as e:
        logger.exception("Erro ao extrair dados da imagem: %s", e)
        await safe_edit_message(query, f"❌ Erro ao analisar imagem: {e}")


async def save(item: Item, query) -> list[Item | bool]:
    try:
        item = await output.save(item)
        await safe_edit_message(
            query,
            f"✅ Item gravado:\n\n{item}\n\nEnvie o nome ou a foto do próximo item:",
        )
        return item, True
    except ValueError as e:
        await safe_edit_message(
            query,
            f"❌ Erro ao gravar item: {str(e)}",
        )
        return item, False


async def debug_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your user ID: {update.effective_user.id}")


# =========================
# Inicialização
# =========================
def main():
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set. Vision features will be disabled.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("myid", debug_user_id))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot iniciado.")
    app.run_polling()


if __name__ == "__main__":
    main()
