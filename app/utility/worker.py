import logging
from queue import Queue
from threading import Thread

queue = Queue()


def worker():
    while True:
        handler, data = queue.get()
        try:
            handler(data)
        except Exception as e:
            logging.error(f"Error processing webhook data: {e}")
        finally:
            queue.task_done()


def start_worker():
    Thread(target=worker, daemon=True).start()
