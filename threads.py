import asyncio
from typing import Coroutine, Any


class Threads:
    def __init__(self):
        self.run_threads = []
        self.main_loop = asyncio.new_event_loop()

        # Set an exception handler for the event loop
        self.main_loop.set_exception_handler(lambda loop, context: True)
        asyncio.set_event_loop(self.main_loop)

    def thread_wait(self, coro: Coroutine, **kwargs) -> None:
        """
        Run a coroutine until complete.
        
        Args:
            coro (Coroutine): The coroutine to run.
            **kwargs: Additional keyword arguments to pass to the coroutine.
        """
        self.main_loop.run_until_complete(coro(**kwargs))

    def add_thread(self, coro: Coroutine, **kwargs) -> asyncio.Task:
        """
        Add a coroutine as a task to be run in the event loop.
        
        Args:
            coro (Coroutine): The coroutine to run.
            **kwargs: Additional keyword arguments to pass to the coroutine.
        
        Returns:
            asyncio.Task: The created task.
        """
        task = asyncio.ensure_future(coro(**kwargs))
        task.add_done_callback(self._callback_task_end)
        self.run_threads.append(task)
        return task

    def terminate(self, task: asyncio.Task) -> None:
        """
        Terminate a specific task.
        
        Args:
            task (asyncio.Task): The task to terminate.
        """
        if not task.cancelled():
            task.cancel()
        try:
            self.run_threads.remove(task)
        except ValueError:
            pass

    def wait_time(self, delay: float) -> None:
        """
        Wait for a specified amount of time.
        
        Args:
            delay (float): The amount of time to wait in seconds.
        """
        self.main_loop.run_until_complete(asyncio.sleep(delay))

    def terminate_all(self) -> None:
        """
        Terminate all running tasks.
        """
        for task in self.run_threads:
            try:
                self.terminate(task)
            except Exception:
                pass

    def _callback_task_end(self, task: asyncio.Task) -> None:
        """
        Callback function for when a task ends.
        
        Args:
            task (asyncio.Task): The task that ended.
        """
        try:
            self.run_threads.remove(task)
        except ValueError:
            pass