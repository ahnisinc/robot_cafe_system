class CoffeeProgressBridge:

    def __init__(self, client):
        self.client = client

    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()
