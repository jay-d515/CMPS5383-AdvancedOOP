"""
resource.py
Defines the Resource hierarchy (parent Resource, subclasses FileResource,
LinkResource, DiscussionPost) and a Commentable interface that any
resource type can support independent of its place in the inheritance
tree.
"""


class Commentable:
    """
    Interface-style mixin. Any class that inherits from this is expected
    to support comments. This is intentionally separate from the Resource
    inheritance tree, so it can be mixed into any resource type.
    """

    def add_comment(self, user, text):
        if not hasattr(self, "comments"):
            self.comments = []
        self.comments.append((user.name, text))
        print(f"  -> {user.name} commented on '{self.title}': {text}")

    def show_comments(self):
        if not getattr(self, "comments", None):
            print("    (no comments yet)")
            return
        for name, text in self.comments:
            print(f"    {name}: {text}")


class Resource:
    """Parent class. Shared metadata for anything posted to a community."""

    def __init__(self, title, uploader):
        self.id = None  # assigned by Database when the resource is saved
        self.title = title
        self.uploader = uploader  # a User object
        self.verified = False

    def display(self):
        """Default display behavior - subclasses override this."""
        print(f"  [Resource] {self.title} (posted by {self.uploader.name})")

    def __str__(self):
        return self.title


class FileResource(Resource):
    """A resource representing an uploaded file (metadata only for now)."""

    def __init__(self, title, uploader, filename):
        super().__init__(title, uploader)
        self.filename = filename

    def display(self):
        tag = " [VERIFIED]" if self.verified else ""
        print(f"  [File] {self.title}{tag} - {self.filename} (by {self.uploader.name})")


class LinkResource(Resource):
    """A resource representing a shared external link."""

    def __init__(self, title, uploader, url):
        super().__init__(title, uploader)
        self.url = url

    def display(self):
        tag = " [VERIFIED]" if self.verified else ""
        print(f"  [Link] {self.title}{tag} - {self.url} (by {self.uploader.name})")


class DiscussionPost(Resource, Commentable):
    """A text post that supports comments via the Commentable interface."""

    def __init__(self, title, uploader, body):
        super().__init__(title, uploader)
        self.body = body
        self.comments = []

    def display(self):
        tag = " [VERIFIED]" if self.verified else ""
        print(f"  [Discussion] {self.title}{tag} (by {self.uploader.name}): {self.body}")
        self.show_comments()