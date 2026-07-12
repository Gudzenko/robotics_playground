from .sdf_helpers import model_file


class Room:
    def __init__(self, name):
        self.name = name
        self._links = []

    def add(self, *links):
        for link in links:
            if link is not None:
                self._links.append(link)
        return self

    def to_sdf(self):
        return model_file(self.name, self._links)
