# Pub/Sub event handling — decoupled agent communication
import asyncio
from datetime import datetime

EVENT_RISK_ASSESSED = "EVENT_RISK_ASSESSED"
EVENT_BATCH_QUARANTINED = "EVENT_BATCH_QUARANTINED"
EVENT_TICKET_CREATED = "EVENT_TICKET_CREATED"

event_log = []

class RecallEventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecallEventBus, cls).__new__(cls)
            cls._instance.queue = asyncio.Queue()
            cls._instance.subscribers = []
        return cls._instance

    async def publish(self, event_type, payload):
        await self.queue.put((event_type, payload))
        
    def publish_sync(self, event_type, payload):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event_type, payload))
        except RuntimeError:
            asyncio.run(self.publish(event_type, payload))

    def subscribe(self, handler):
        self.subscribers.append(handler)

    async def start(self):
        while True:
            event_type, payload = await self.queue.get()
            for handler in self.subscribers:
                try:
                    await handler(event_type, payload)
                except Exception as e:
                    print(f"Error in event handler: {e}")
            self.queue.task_done()

event_bus = RecallEventBus()

async def log_event_handler(event_type, payload):
    timestamp = datetime.now().strftime("%H:%M:%S")
    event_log.append({"time": timestamp, "type": event_type, "payload": payload})

event_bus.subscribe(log_event_handler)
