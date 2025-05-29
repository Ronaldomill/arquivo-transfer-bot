
import asyncio
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = 21755559
API_HASH = "1b1fca82cddb5bf5ff782e53a64f0ce0"
BOT_TOKEN = "7851982224:AAEKr7TqJRVgH8yaqILJPk1-A0RUBiF9lSY"

CANAL_ORIGEM = -1001902473123
GRUPO_DESTINO = -1002517527737

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.app = Client("meu_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
        self.topicos_cache = {}

    async def start(self):
        await self.app.start()
        logger.info("🤖 Bot iniciado com sucesso!")
        await self.mapear_topicos()
        await self.varrer_mensagens_antigas(limite=100)
        self.configurar_handlers()

    async def mapear_topicos(self):
        logger.info("📋 Mapeando tópicos...")
        async for msg in self.app.get_chat_history(GRUPO_DESTINO, limit=200):
            if msg.reply_to_message_id:
                topic_id = msg.reply_to_message_id
                try:
                    info = await self.app.get_messages(GRUPO_DESTINO, topic_id)
                    if hasattr(info, 'forum_topic_created'):
                        nome = info.forum_topic_created.title
                        self.topicos_cache[nome.lower()] = topic_id
                        logger.info(f"🧷 Tópico encontrado: {nome}")
                except: continue
        logger.info(f"✅ Total: {len(self.topicos_cache)} tópicos mapeados.")

    def configurar_handlers(self):
        @self.app.on_message(filters.chat(CANAL_ORIGEM))
        async def ao_receber(_, message: Message):
            texto = message.text or message.caption or ""
            hashtags = self.extrair_hashtags(texto)
            for tag in hashtags:
                await self.enviar_para_topico(message, tag)

    def extrair_hashtags(self, texto):
        return re.findall(r"#(\w+)", texto.lower())

    async def enviar_para_topico(self, msg: Message, hashtag: str):
        topic_id = self.topicos_cache.get(hashtag.lower())
        if not topic_id:
            logger.warning(f"⚠️ Tópico '{hashtag}' não encontrado.")
            return
        texto = msg.text or msg.caption or ""
        texto_limpo = re.sub(rf"#{hashtag}\b", "", texto, flags=re.IGNORECASE).strip()
        try:
            if msg.photo:
                await self.app.send_photo(GRUPO_DESTINO, msg.photo.file_id, caption=texto_limpo or None, reply_to_message_id=topic_id)
            elif msg.video:
                await self.app.send_video(GRUPO_DESTINO, msg.video.file_id, caption=texto_limpo or None, reply_to_message_id=topic_id)
            elif msg.document:
                await self.app.send_document(GRUPO_DESTINO, msg.document.file_id, caption=texto_limpo or None, reply_to_message_id=topic_id)
            elif texto_limpo:
                await self.app.send_message(GRUPO_DESTINO, texto_limpo, reply_to_message_id=topic_id)
            logger.info(f"✅ Enviado para tópico #{hashtag}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar #{hashtag}: {e}")

    async def varrer_mensagens_antigas(self, limite=100):
        logger.info("🔁 Varrendo mensagens antigas...")
        async for msg in self.app.get_chat_history(CANAL_ORIGEM, limit=limite):
            texto = msg.text or msg.caption or ""
            hashtags = self.extrair_hashtags(texto)
            for tag in hashtags:
                await self.enviar_para_topico(msg, tag)
        logger.info("✅ Varredura completa.")

    async def run_forever(self):
        await self.start()
        logger.info("🚀 Rodando bot...")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(TelegramBot().run_forever())
