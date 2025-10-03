class FakeUser:
    def __init__(self, username, image=None):
        self.username = username
        self.image = image


class FakeBin:
    def __init__(self, meta, hash):
        self.title = meta.get("title")
        self.author = FakeUser(meta.get("author"), meta.get("author_image"))
        self.created_at = meta.get("created_at")
        self.hash = hash
        self.size_bin = meta.get("size_bin", 0)
        self.language = meta.get("language", "")
        self.category = meta.get("category", "")
        self.tags = meta.get("tags", "")
        self.get_language_display = lambda: meta.get("language_display", self.language)
        self.get_category_display = lambda: meta.get("category_display", self.category)
        self.comments = []
