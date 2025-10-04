import asyncio

from knowledge_base.bot import kb_bot
from knowledge_base.main import knowledge_base_test

if __name__ == "__main__":
    asyncio.run(kb_bot())
