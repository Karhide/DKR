
class ImageRegistry:

    def __init__(self):
        pass

    def query(self, name):
        raise NotImplementedError("Abstract class")

    def name(self):
        raise NotImplementedError("Abstract class")