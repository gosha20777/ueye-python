from pyueye import ueye


class ImageBuffer:
    """
    A class to manage the memory of an image buffer.
    """
    def __init__(self) -> None:
        self.mem_ptr = ueye.c_mem_p()
        self.mem_id = ueye.int()