class Rect:
    """
    A rectangle class.
    """
    def __init__(
            self, 
            x: int = 0, 
            y: int = 0, 
            width: int = 0, 
            height: int = 0
    ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height