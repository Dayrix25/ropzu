import asyncio
import io
import os
import random
import re
import logging

from dotenv import load_dotenv
from telethon import TelegramClient, events, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from PIL import Image
import pytesseract

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

TESSERACT_PATH = os.getenv("TESSERACT_PATH", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

DEBUG_ALL_MESSAGES = False

LAST_START = {"bot": None, "param": None}

SUBSCRIBE_MARKERS = [
    "нужно подписаться", "подпишитесь", "для участия",
    "попробуйте снова", "выполните условия",
    "не выполнены условия", "подписки",
    "обновляю список", "проверяю выполнение",
]

CAPTCHA_MARKERS = [
    "какие числа", "какие цифры", "отправьте боту ответ",
    "введите ответ", "напишите ответ", "решите пример",
    "сколько будет", "введите число", "введите цифры", "что вы видите",
]

EMOJI_CAPTCHA_MARKERS = [
    "выберите эмодзи", "нажми на кнопку", "где изображ",
    "какой эмодзи", "выберите", "нажмите на кнопку",
    "нужно убедиться", "не робот",
]

CAPTCHA_FAIL_MARKERS = [
    "неверно", "не пройдена", "попробуйте ещё", "попробуйте еще",
]

ALREADY_MARKERS = [
    "успешно приняли участие", "вы участвуете", "участие принято",
    "вы в игре", "поздравляем",
    "уже приняли участие", "уже участвуете", "вы уже участвуете",
    "вы уже приняли",
]

EMOJI_MAP = {
    "яблоко": ["🍎", "🍏", "🍐"],
    "банан": ["🍌"],
    "апельсин": ["🍊", "🍋"],
    "вишня": ["🍒"],
    "клубника": ["🍓"],
    "ягод": ["🍓", "🍒", "🫐", "🍇"],
    "арбуз": ["🍉"],
    "пицца": ["🍕"],
    "бургер": ["🍔"],
    "торт": ["🎂", "🍰", "🧁"],
    "виноград": ["🍇"],
    "морковь": ["🥕"],
    "хлеб": ["🍞", "🥖", "🥐"],
    "сыр": ["🧀"],
    "яйцо": ["🥚", "🍳"],
    "рыба": ["🐟", "🐠", "🐡", "🦈"],
    "суши": ["🍣", "🍱"],
    "мороженое": ["🍦", "🍧", "🍨"],
    "конфета": ["🍬", "🍭", "🍫"],
    "кофе": ["☕"],
    "чай": ["🍵"],
    "лев": ["🦁"],
    "тигр": ["🐯", "🐅"],
    "кот": ["🐱", "🐈", "😺", "😸", "😻"],
    "кошка": ["🐱", "🐈", "😺", "😸", "😻"],
    "котенок": ["🐱", "🐈", "😺"],
    "собака": ["🐶", "🐕", "🦮", "🐩"],
    "щенок": ["🐶", "🐕"],
    "волк": ["🐺"],
    "лиса": ["🦊"],
    "медведь": ["🐻", "🐻‍❄️"],
    "панда": ["🐼"],
    "обезьяна": ["🐵", "🐒", "🙈", "🙉", "🙊"],
    "слон": ["🐘"],
    "жираф": ["🦒"],
    "зебра": ["🦓"],
    "лошадь": ["🐴", "🐎", "🦄"],
    "единорог": ["🦄"],
    "корова": ["🐮", "🐄"],
    "свинья": ["🐷", "🐖"],
    "овца": ["🐑", "🐏"],
    "коза": ["🐐"],
    "курица": ["🐔", "🐓", "🐣", "🐤", "🐥"],
    "птица": ["🐦", "🐤", "🐥", "🦅", "🕊"],
    "петух": ["🐓"],
    "утка": ["🦆"],
    "сова": ["🦉"],
    "орел": ["🦅"],
    "попугай": ["🦜"],
    "мышь": ["🐭", "🐁"],
    "крыса": ["🐀"],
    "хомяк": ["🐹"],
    "кролик": ["🐰", "🐇"],
    "заяц": ["🐰", "🐇"],
    "ежик": ["🦔"],
    "черепаха": ["🐢"],
    "змея": ["🐍"],
    "ящерица": ["🦎"],
    "динозавр": ["🦕", "🦖"],
    "дракон": ["🐉", "🐲"],
    "кит": ["🐋", "🐳"],
    "дельфин": ["🐬"],
    "акула": ["🦈"],
    "осьминог": ["🐙"],
    "краб": ["🦀"],
    "креветка": ["🦐", "🦞"],
    "улитка": ["🐌"],
    "бабочка": ["🦋"],
    "пчела": ["🐝"],
    "жук": ["🐞", "🪲"],
    "паук": ["🕷", "🕸"],
    "муравей": ["🐜"],
    "скорпион": ["🦂"],
    "луна": ["🌙", "🌕", "🌑", "🌒", "🌓", "🌔", "🌖", "🌗", "🌘", "🌚", "🌛", "🌜"],
    "солнце": ["☀️", "☀", "🌞", "🌤", "⛅", "🌥", "🌦"],
    "звезда": ["⭐", "🌟", "✨", "💫"],
    "звезду": ["⭐", "🌟", "✨", "💫"],
    "облако": ["☁️", "☁", "🌥", "⛅"],
    "дождь": ["🌧", "☔", "🌦"],
    "гроза": ["⛈", "🌩"],
    "молния": ["⚡", "🌩"],
    "снег": ["❄️", "❄", "🌨", "⛄", "☃️"],
    "снежинка": ["❄️", "❄"],
    "радуга": ["🌈"],
    "огонь": ["🔥"],
    "вода": ["💧", "🌊", "💦"],
    "дерево": ["🌳", "🌲", "🎄", "🌴"],
    "елка": ["🎄", "🌲"],
    "пальма": ["🌴"],
    "кактус": ["🌵"],
    "цветок": ["🌸", "🌺", "🌻", "🌼", "🌷", "💐", "🌹"],
    "роза": ["🌹", "🥀"],
    "лист": ["🍀", "🍁", "🍂", "🍃"],
    "клевер": ["🍀"],
    "гриб": ["🍄"],
    "машина": ["🚗", "🚙", "🚕", "🏎", "🚓", "🚔"],
    "машин": ["🚗", "🚙", "🚕", "🏎", "🚓", "🚔"],
    "авто": ["🚗", "🚙", "🚕", "🏎", "🚓", "🚔"],
    "такси": ["🚕"],
    "автобус": ["🚌", "🚍", "🚎"],
    "грузовик": ["🚚", "🚛"],
    "поезд": ["🚂", "🚃", "🚄", "🚅", "🚆", "🚇", "🚈"],
    "самолет": ["✈️", "✈", "🛫", "🛬", "🛩"],
    "вертолет": ["🚁"],
    "ракета": ["🚀"],
    "корабль": ["🚢", "⛴", "🛳"],
    "лодка": ["⛵", "🚤", "🛶"],
    "велосипед": ["🚲", "🚴"],
    "мотоцикл": ["🏍", "🛵"],
    "трактор": ["🚜"],
    "скорая": ["🚑"],
    "пожарная": ["🚒"],
    "полиция": ["🚓", "🚔", "👮"],
    "гитара": ["🎸"],
    "пианино": ["🎹"],
    "барабан": ["🥁"],
    "скрипка": ["🎻"],
    "труба": ["🎺"],
    "микрофон": ["🎤"],
    "наушники": ["🎧"],
    "часы": ["⌚", "⏰", "⏱", "🕐"],
    "телефон": ["📱", "☎️", "📞"],
    "компьютер": ["💻", "🖥", "⌨️"],
    "камера": ["📷", "📸", "📹", "🎥"],
    "лампа": ["💡", "🔦"],
    "свеча": ["🕯"],
    "ключ": ["🔑", "🗝"],
    "замок": ["🔒", "🔓", "🔐", "🏰", "🏯"],
    "нож": ["🔪", "🗡"],
    "молоток": ["🔨", "⚒", "🛠"],
    "чашка": ["☕", "🍵", "🥤", "🍶"],
    "бутылка": ["🍾", "🍼", "🧴"],
    "книга": ["📖", "📚", "📕", "📗", "📘", "📙"],
    "ручка": ["🖊", "🖋", "✏️", "✒️"],
    "ножницы": ["✂️", "✂"],
    "мяч": ["⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🎱"],
    "футбол": ["⚽"],
    "баскетбол": ["🏀"],
    "теннис": ["🎾"],
    "подарок": ["🎁"],
    "деньги": ["💰", "💵", "💴", "💶", "💷", "🪙"],
    "корона": ["👑"],
    "кольцо": ["💍"],
    "сердце": ["❤️", "❤", "💖", "💕", "🩷", "♥️", "💘", "💝"],
    "крест": ["✝️", "☦️", "❌", "✖️"],
    "галочка": ["✅", "☑️", "✔️"],
}


def parse_channel(c):
    c = c.strip()
    if not c:
        return None
    if re.fullmatch(r'-?\d+', c):
        return int(c)
    c = re.sub(r'^https?://t\.me/', '', c)
    c = c.lstrip('@')
    return c


CHANNELS = list(dict.fromkeys(
    x for x in (parse_channel(c) for c in os.getenv("GIVEAWAY_CHANNELS", "").split(",")) if x is not None
))

GIVEAWAY_BOTS = list(dict.fromkeys(
    x for x in (parse_channel(b) for b in os.getenv("GIVEAWAY_BOTS", "").split(",")) if x is not None
))

DELAY_AFTER_JOIN = (5, 15)
DELAY_BEFORE_CLICK = (3, 8)
DELAY_BETWEEN_ACTIONS = (10, 15)
DELAY_BEFORE_RESEND_START = (5, 10)

DELAY_BEFORE_CAPTCHA_CLICK = (3, 5)
DELAY_AFTER_CAPTCHA_CLICK = (3, 3)
DELAY_BEFORE_CAPTCHA_RETRY = (3, 5)

stats = {"found": 0, "joined": 0, "participated": 0, "failed": 0,
         "floodwaits": 0, "captcha_solved": 0, "captcha_failed": 0, "resubmits": 0}


async def random_delay(min_sec, max_sec, reason=""):
    delay = random.uniform(min_sec, max_sec)
    if reason:
        log.info(f"⏳ Пауза {delay:.1f} сек ({reason})...")
    await asyncio.sleep(delay)


def extract_channels(text, entities=None):
    """Извлекает каналы из текста и entities (скрытые ссылки)."""
    usernames = set()
    invites = set()

    # 1) Из обычного текста
    usernames.update(re.findall(r'@([A-Za-z0-9_]{5,})', text))
    usernames.update(re.findall(r't\.me/([A-Za-z0-9_]{5,})', text))
    invites.update(re.findall(r't\.me/(?:\+|joinchat/)([A-Za-z0-9_-]+)', text))

    # 2) Из entities — скрытые ссылки (MessageEntityTextUrl)
    if entities:
        for ent in entities:
            url = getattr(ent, "url", None)
            if not url:
                continue
            m = re.search(r't\.me/([A-Za-z0-9_]{5,})', url)
            if m:
                usernames.add(m.group(1))
            m = re.search(r't\.me/(?:\+|joinchat/)([A-Za-z0-9_-]+)', url)
            if m:
                invites.add(m.group(1))

    # Убираем самих ботов из списка
    usernames.discard("FastGiveawaysBot")
    usernames.discard("BestRandom_bot")

    return list(usernames), list(invites)


async def safe_join(client, username):
    try:
        await client(JoinChannelRequest(username))
        log.info(f"   ✅ Подписался: @{username}")
        stats["joined"] += 1
        await random_delay(*DELAY_AFTER_JOIN, reason="после подписки")
        return True
    except errors.UserAlreadyParticipantError:
        log.info(f"   ⏭️ Уже подписан: @{username}")
        return True
    except errors.ChannelPrivateError:
        log.warning(f"   🔒 Приватный: @{username}")
        return False
    except errors.FloodWaitError as e:
        log.warning(f"   🚫 FloodWait {e.seconds} сек")
        stats["floodwaits"] += 1
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        log.warning(f"   ⚠️ Ошибка @{username}: {e}")
        return False


async def safe_join_invite(client, invite_hash):
    try:
        await client(ImportChatInviteRequest(invite_hash))
        log.info(f"   ✅ Подписался по инвайту")
        stats["joined"] += 1
        await random_delay(*DELAY_AFTER_JOIN, reason="после подписки")
        return True
    except errors.UserAlreadyParticipantError:
        log.info(f"   ⏭️ Уже подписан по инвайту")
        return True
    except errors.FloodWaitError as e:
        log.warning(f"   🚫 FloodWait {e.seconds} сек")
        stats["floodwaits"] += 1
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        log.warning(f"   ⚠️ Ошибка инвайта: {e}")
        return False


def get_button_info(btn):
    btn_type = type(btn).__name__
    url = getattr(btn, "url", None)
    if not url and hasattr(btn, "button"):
        url = getattr(btn.button, "url", None)
    return btn_type, url


def find_first_button(event):
    if not event.buttons:
        return None
    for row in event.buttons:
        for btn in row:
            return btn
    return None


async def handle_button_click(client, target_btn, context=""):
    btn_type, url = get_button_info(target_btn)
    log.info(f"   🔘 Тип кнопки{context}: {btn_type}, url={url!r}")

    if url:
        m = re.match(r'https?://t\.me/([A-Za-z0-9_]+)\?start=(.+)', url)
        if m:
            bot_username = m.group(1)
            start_param = m.group(2)

            log.info(f"   🤖 Deep-link → /start {start_param} боту @{bot_username}")
            try:
                await client.send_message(bot_username, f"/start {start_param}")
                log.info("   ✅ /start отправлен!")
                LAST_START["bot"] = bot_username
                LAST_START["param"] = start_param
                return True
            except Exception as e:
                log.warning(f"   ⚠️ Ошибка /start: {e}")
                return False
        else:
            log.info(f"   ⚠️ URL без start: {url}")
            return False

    try:
        await target_btn.click()
        log.info("   🎉 Click отправлен")
        return True
    except errors.FloodWaitError as e:
        log.warning(f"   🚫 FloodWait {e.seconds} сек")
        stats["floodwaits"] += 1
        await asyncio.sleep(e.seconds)
        return False
    except errors.DataInvalidError:
        log.info("   ℹ️ Кнопка устарела")
        return False
    except Exception as e:
        log.warning(f"   ⚠️ Ошибка клика: {e}")
        return False


def preprocess_image(img):
    img = img.convert('L')
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS)
    img = img.point(lambda x: 0 if x < 140 else 255, '1')
    return img


def ocr_image(img):
    img = preprocess_image(img)
    configs = [
        '--psm 7 -c tessedit_char_whitelist=0123456789',
        '--psm 8 -c tessedit_char_whitelist=0123456789',
        '--psm 6 -c tessedit_char_whitelist=0123456789',
        '--psm 13 -c tessedit_char_whitelist=0123456789',
    ]
    results = []
    for cfg in configs:
        try:
            text = pytesseract.image_to_string(img, config=cfg).strip()
            digits = re.sub(r'\D', '', text)
            if digits:
                results.append(digits)
        except Exception as e:
            log.warning(f"   ⚠️ OCR ({cfg}): {e}")

    if not results:
        return None
    from collections import Counter
    most_common = Counter(results).most_common(1)[0]
    log.info(f"   🔍 OCR: {results} → {most_common[0]!r}")
    return most_common[0]


async def solve_number_captcha(event):
    try:
        photo_bytes = await event.download_media(bytes)
        if not photo_bytes:
            return None
        img = Image.open(io.BytesIO(photo_bytes))
        log.info(f"   🖼 Картинка: {img.size}")
        return ocr_image(img)
    except Exception as e:
        log.warning(f"   ⚠️ Ошибка OCR: {e}")
        return None


async def solve_emoji_captcha(event):
    """Жмёт первую попавшуюся кнопку капчи (кроме Откат/Отмена).
    С паузами перед и после нажатия, чтобы бот успел обработать."""
    text = (event.raw_text or "").lower()

    if not event.buttons:
        log.warning("   ⚠️ Капча без кнопок")
        return False

    candidates = []
    for word, emojis in EMOJI_MAP.items():
        if word in text:
            candidates.extend(emojis)

    target_btn = None
    if candidates:
        log.info(f"   🎯 Ищу кнопку с: {candidates}")
        for row in event.buttons:
            for btn in row:
                for emo in candidates:
                    if emo in (btn.text or ""):
                        target_btn = btn
                        break
                if target_btn:
                    break
            if target_btn:
                break

    if not target_btn:
        log.info("   ⚠️ Эмодзи кастомный, беру первую подходящую кнопку...")
        skip_words = ["откат", "отмена", "назад", "cancel"]
        for row in event.buttons:
            for btn in row:
                btn_text = (btn.text or "").lower().strip()
                if any(sw in btn_text for sw in skip_words):
                    continue
                target_btn = btn
                break
            if target_btn:
                break

    if not target_btn:
        log.info("   ❌ Нет подходящих кнопок")
        return False

    await random_delay(*DELAY_BEFORE_CAPTCHA_CLICK, reason="перед нажатием кнопки капчи")

    log.info(f"   🎯 Жму: {target_btn.text!r}")
    try:
        await target_btn.click()
        log.info("   ✅ Нажал, жду ответ...")
        await random_delay(*DELAY_AFTER_CAPTCHA_CLICK, reason="после нажатия, жду обработки")
        return True
    except errors.FloodWaitError as e:
        stats["floodwaits"] += 1
        await asyncio.sleep(e.seconds)
        return False
    except errors.DataInvalidError:
        log.info("   ℹ️ Кнопка устарела")
        return False
    except Exception as e:
        log.warning(f"   ⚠️ Ошибка клика: {e}")
        return False


async def main():
    if not CHANNELS:
        raise SystemExit("Укажи GIVEAWAY_CHANNELS в .env")

    log.info(f"🎯 Каналов: {len(CHANNELS)}, ботов: {len(GIVEAWAY_BOTS)}")

    try:
        version = pytesseract.get_tesseract_version()
        log.info(f"✅ Tesseract: {version}")
    except Exception as e:
        log.error(f"❌ Tesseract не работает: {e}")
        return

    client = TelegramClient("session_giveaway", API_ID, API_HASH)
    await client.start()
    log.info("✅ Подключено")

    log.info("🔥 Прогреваю каналы...")
    for ch in CHANNELS:
        try:
            entity = await client.get_entity(ch)
            log.info(f"   ✅ {getattr(entity, 'title', ch)}")
        except Exception as e:
            log.warning(f"   ⚠️ {ch}: {e}")

    if DEBUG_ALL_MESSAGES:
        @client.on(events.NewMessage(chats=CHANNELS))
        async def debug_handler(event):
            text = event.raw_text or ""
            chat_name = event.chat.title if event.chat else str(event.chat_id)
            log.info(f"👀 [{chat_name}] {text[:150]!r}")
            if event.buttons:
                btns = [btn.text for row in event.buttons for btn in row]
                log.info(f"   🔘 event.buttons: {btns}")

    @client.on(events.NewMessage(chats=CHANNELS))
    async def giveaway_handler(event):
        text = event.raw_text or ""
        if not event.buttons:
            return

        target_btn = find_first_button(event)
        if not target_btn:
            return

        stats["found"] += 1
        chat_name = event.chat.title if event.chat else str(event.chat_id)
        log.info(f"🎁 Розыгрыш в «{chat_name}»")

        usernames, invites = extract_channels(text, event.message.entities)
        if usernames or invites:
            log.info(f"   📎 Условия: {len(usernames)} каналов")
            for u in usernames:
                await safe_join(client, u)
            for h in invites:
                await safe_join_invite(client, h)

        await random_delay(*DELAY_BEFORE_CLICK, reason="перед нажатием")
        ok = await handle_button_click(client, target_btn, context=" в канале")
        if ok:
            log.info("   🎉 Участие принято!")
            stats["participated"] += 1
        else:
            stats["failed"] += 1

        await random_delay(*DELAY_BETWEEN_ACTIONS, reason="после участия")

    if GIVEAWAY_BOTS:
        async def process_bot_message(event, source="new"):
            text = event.raw_text or ""
            sender = await event.get_sender()
            sender_name = getattr(sender, "username", None) or str(event.sender_id)
            log.info(f"📩 [{source} DM @{sender_name}] {text[:150]!r}")

            text_lower = text.lower()

            if any(m in text_lower for m in ALREADY_MARKERS):
                log.info("   ✅ Уже участвуем — ничего не делаю")
                return

            if any(m in text_lower for m in CAPTCHA_FAIL_MARKERS):
                log.info("   ❌ Капча провалена, переотправляю /start...")
                if LAST_START["bot"] and LAST_START["param"]:
                    await random_delay(*DELAY_BEFORE_CAPTCHA_RETRY, reason="перед новой попыткой")
                    try:
                        await client.send_message(
                            LAST_START["bot"],
                            f"/start {LAST_START['param']}"
                        )
                        log.info("   🔁 /start отправлен, жду новую капчу")
                    except Exception as e:
                        log.warning(f"   ⚠️ Ошибка переотправки: {e}")
                else:
                    log.warning("   ⚠️ Нет сохранённого start-параметра")
                return

            if any(m in text_lower for m in EMOJI_CAPTCHA_MARKERS) and event.buttons:
                log.info("   🎨 Капча с эмодзи, решаю...")
                ok = await solve_emoji_captcha(event)
                if ok:
                    stats["captcha_solved"] += 1
                else:
                    stats["captcha_failed"] += 1
                return

            if any(m in text_lower for m in CAPTCHA_MARKERS):
                log.info("   🔢 Капча с цифрами, распознаю...")
                answer = await solve_number_captcha(event)
                if answer and answer.isdigit():
                    log.info(f"   🎯 Распознал: {answer!r}")
                    await random_delay(1, 3, reason="перед отправкой")
                    try:
                        await event.reply(answer)
                        log.info("   ✅ Отправлено!")
                        stats["captcha_solved"] += 1
                    except Exception as e:
                        log.warning(f"   ⚠️ Ошибка отправки: {e}")
                        stats["captcha_failed"] += 1
                else:
                    log.warning(f"   ❌ Не распознал: {answer!r}")
                    stats["captcha_failed"] += 1
                return

            if any(m in text_lower for m in SUBSCRIBE_MARKERS):
                log.info("   📢 Требуется подписка, извлекаю...")
                usernames, invites = extract_channels(text, event.message.entities)

                if usernames or invites:
                    log.info(f"   📎 Найдено: {len(usernames)} каналов, {len(invites)} инвайтов")
                    for u in usernames:
                        await safe_join(client, u)
                    for h in invites:
                        await safe_join_invite(client, h)

                    if LAST_START["bot"] and LAST_START["param"]:
                        log.info(f"   🔁 Переотправляю /start {LAST_START['param']} боту @{LAST_START['bot']}")
                        await random_delay(*DELAY_BEFORE_RESEND_START, reason="перед повторной отправкой")
                        try:
                            await client.send_message(
                                LAST_START["bot"],
                                f"/start {LAST_START['param']}"
                            )
                            log.info("   ✅ /start переотправлен!")
                            stats["resubmits"] += 1
                        except Exception as e:
                            log.warning(f"   ⚠️ Ошибка переотправки: {e}")
                    else:
                        log.warning("   ⚠️ Нет сохранённого start-параметра")
                else:
                    log.info("   ⚠️ Каналов в тексте не найдено")
                return

            if not event.buttons:
                log.info("   ⚠️ Кнопок нет")
                return

            usernames, invites = extract_channels(text, event.message.entities)
            if usernames or invites:
                for u in usernames:
                    await safe_join(client, u)
                for h in invites:
                    await safe_join_invite(client, h)

            target_btn = find_first_button(event)
            if not target_btn:
                return

            await random_delay(*DELAY_BEFORE_CLICK, reason="перед кликом в ЛС")
            ok = await handle_button_click(client, target_btn, context=" в ЛС")
            if ok:
                log.info("   🎉 Действие в боте выполнено!")
                stats["participated"] += 1
            else:
                stats["failed"] += 1

            await random_delay(*DELAY_BETWEEN_ACTIONS, reason="после действия")

        @client.on(events.NewMessage(from_users=GIVEAWAY_BOTS))
        async def bot_dm_handler(event):
            await process_bot_message(event, source="new")

        @client.on(events.MessageEdited(from_users=GIVEAWAY_BOTS))
        async def bot_edit_handler(event):
            await process_bot_message(event, source="edited")

    log.info("🤖 Запущено. Ctrl+C — стоп.")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info(f"📊 Статистика: {stats}")