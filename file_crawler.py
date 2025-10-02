import asyncio

from knowledge_base.load import crawl_folder

if __name__ == "__main__":
    asyncio.run(crawl_folder("C:\\Users\\vraj0\\IdeaProjects\\fag_2", [".py", ".yaml"]))
