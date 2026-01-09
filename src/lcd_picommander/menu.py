"""Menu structure and node representation."""


class MenuNode:
    """Represents a single item in the menu tree."""
    def __init__(self, label, action=None, children=None, wait_for_key=False):
        self.label = label
        self.action = action
        self.children = children if children else []
        self.wait_for_key = wait_for_key

    @property
    def is_submenu(self):
        return bool(self.children)
