import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TaskQueue:
    def __init__(self, max_concurrent_tasks=3):
        self.queue = asyncio.Queue()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running_tasks = set()

    async def add_task(self, coro):
        await self.queue.put(coro)

    async def run(self):
        while True:
            if len(self.running_tasks) < self.max_concurrent_tasks and not self.queue.empty():
                coro = await self.queue.get()
                task = asyncio.create_task(self._run_task(coro))
                self.running_tasks.add(task)
            else:
                await asyncio.sleep(1)  # Wait before checking again

    async def _run_task(self, coro):
        try:
            await coro
        except Exception as e:
            logger.error(f"Task error: {str(e)}")
        finally:
            self.running_tasks.remove(asyncio.current_task())

task_queue = TaskQueue()