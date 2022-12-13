import numpy as np
from pyueye import ueye
from .utils import get_bits_per_pixel
from .image_buffer import ImageBuffer
from .exceptions import UEyeError

class MemoryInfo:
    """
    A class to manage the memory information of an image buffer.
    """
    def __init__(self, h_cam, img_buff: ImageBuffer) -> None:
        self.x = ueye.int()
        self.y = ueye.int()
        self.bits = ueye.int()
        self.pitch = ueye.int()
        self.img_buff = img_buff
        rect_aoi = ueye.IS_RECT()
        ret = ueye.is_AOI(h_cam,
                          ueye.IS_AOI_IMAGE_GET_AOI,
                          rect_aoi, ueye.sizeof(rect_aoi))
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)
        self.width = rect_aoi.s32Width.value
        self.height = rect_aoi.s32Height.value
        ret = ueye.is_InquireImageMem(h_cam,
                                      self.img_buff.mem_ptr,
                                      self.img_buff.mem_id,
                                      self.x, self.y,
                                      self.bits, self.pitch)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)


class ImageData:
    """
    A class to manage the data of an image buffer.
    """
    def __init__(self, h_cam: ueye.HIDS, img_buff: ImageBuffer) -> None:
        self.h_cam = h_cam
        self.img_buff = img_buff
        self.mem_info = MemoryInfo(h_cam, img_buff)
        self.color_mode = ueye.is_SetColorMode(h_cam, ueye.IS_GET_COLOR_MODE)
        self.bits_per_pixel = get_bits_per_pixel(self.color_mode)
        self.array = ueye.get_data(self.img_buff.mem_ptr,
                                   self.mem_info.width,
                                   self.mem_info.height,
                                   self.mem_info.bits,
                                   self.mem_info.pitch,
                                   True)

    def as_np_image(self) -> np.ndarray:
        """
        Return the image buffer as a numpy array.
        """
        channels = int((7 + self.bits_per_pixel) / 8)
        
        
        if channels > 1:
            return np.reshape(self.array, (self.mem_info.height,
                                              self.mem_info.width, channels))
        else:
            return np.reshape(self.array, (self.mem_info.height,
                                              self.mem_info.width))

    def unlock(self) -> None:
        """
        Unlock the image buffer.
        """
        ret = ueye.is_UnlockSeqBuf(self.h_cam, self.img_buff.mem_id,
                                   self.img_buff.mem_ptr)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)