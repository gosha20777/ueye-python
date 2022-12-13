from pyueye import ueye
from typing import List
from .exceptions import UEyeError
from .image_buffer import ImageBuffer
from .image_data import ImageData
from .rect import Rect
from .utils import get_bits_per_pixel


class Camera:
    """
    Camera class.
    """
    def __init__(
        self, 
        device_id: int = 0, 
        buffer_count: int = 3
    ) -> None:
        """
        Parameters
        ==========
        device_id: int
            Camera device id.
        buffer_count: int
            Number of buffers to allocate.
        """
        self.h_cam = ueye.HIDS(device_id)
        self.buffer_count = buffer_count
        self.img_buffers = []
        self.current_fps = None

    def __enter__(self) -> None:
        """
        Open the connection to the camera.
        Raises
        ======
        UEyeError
        """
        ret = ueye.is_InitCamera(self.h_cam, None)
        if ret != ueye.IS_SUCCESS:
            self.h_cam = None
            raise UEyeError(ret)
        return self

    def __exit__(self, _type, value, traceback):
        if self.h_cam is not None:
            ret = ueye.is_ExitCamera(self.h_cam)
        if ret == ueye.IS_SUCCESS:
            self.h_cam = None
        else:
            raise UEyeError(ret)

    @property
    def camera(self) -> ueye.HIDS:
        """
        Return the camera handle.
        Returns
        =======
        h_cam: ueye.HIDS
        """
        return self.h_cam

    def alloc(self) -> None:
        """
        Allocate memory for futur images.
        """
        # Get camera settings
        rect = self.get_aoi()
        bpp = get_bits_per_pixel(self.get_colormode())
        # Check that already existing buffers are free
        for buff in self.img_buffers:
            ret = ueye.is_FreeImageMem(self.h_cam, buff.mem_ptr, buff.mem_id)
            if ret != ueye.IS_SUCCESS:
                raise UEyeError(ret)

        self.img_buffers = []
        # Create asked buffers
        for i in range(self.buffer_count):
            buff = ImageBuffer()
            ueye.is_AllocImageMem(self.h_cam,
                                  rect.width, rect.height, bpp,
                                  buff.mem_ptr, buff.mem_id)
            ret = ueye.is_AddToSequence(self.h_cam, buff.mem_ptr, buff.mem_id)
            if ret != ueye.IS_SUCCESS:
                raise UEyeError(ret)
            self.img_buffers.append(buff)

        ueye.is_InitImageQueue(self.h_cam, 0)

    def get_aoi(self) -> Rect:
        """
        Get the current area of interest.
        Returns
        =======
        rect: Rect object
            Area of interest
        """
        rect_aoi = ueye.IS_RECT()
        ueye.is_AOI(self.h_cam, ueye.IS_AOI_IMAGE_GET_AOI, rect_aoi,
                    ueye.sizeof(rect_aoi))
        return Rect(rect_aoi.s32X.value,
                    rect_aoi.s32Y.value,
                    rect_aoi.s32Width.value,
                    rect_aoi.s32Height.value)

    def set_aoi(self, x, y, width, height) -> None:
        """
        Set the area of interest.
        Parameters
        ==========
        x, y, width, height: integers
            Position and size of the area of interest.
        """
        rect_aoi = ueye.IS_RECT()
        rect_aoi.s32X = ueye.int(x)
        rect_aoi.s32Y = ueye.int(y)
        rect_aoi.s32Width = ueye.int(width)
        rect_aoi.s32Height = ueye.int(height)
        ueye.is_AOI(self.h_cam, ueye.IS_AOI_IMAGE_SET_AOI, rect_aoi,
                           ueye.sizeof(rect_aoi))

    def set_fps(self, fps):
        """
        Set the fps.
        Returns
        =======
        fps: number
            Real fps, can be slightly different than the asked one.
        """
        # checking available fps
        mini, maxi = self.get_fps_range()
        if fps < mini:
            print(f'Warning: Specified fps ({fps:.2f}) not in possible range:'
                  f' [{mini:.2f}, {maxi:.2f}].'
                  f' fps has been set to {mini:.2f}.')
            fps = mini
        if fps > maxi:
            print(f'Warning: Specified fps ({fps:.2f}) not in possible range:'
                  f' [{mini:.2f}, {maxi:.2f}].'
                  f' fps has been set to {maxi:.2f}.')
            fps = maxi
        fps = ueye.c_double(fps)
        new_fps = ueye.c_double()
        ret = ueye.is_SetFrameRate(self.h_cam, fps, new_fps)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)
        self.current_fps = float(new_fps)

    def get_fps(self) -> float:
        """
        Get the current fps.
        Returns
        =======
        fps: number
            Current fps.
        """
        if self.current_fps is not None:
            return self.current_fps
        fps = ueye.c_double()
        ret = ueye.is_GetFramesPerSecond(self.h_cam, fps)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)
        return fps

    def get_fps_range(self) -> List[float]:
        """
        Get the current fps available range.
        Returns
        =======
        fps_range: 2x1 array
            range of available fps
        """
        mini = ueye.c_double()
        maxi = ueye.c_double()
        interv = ueye.c_double()
        ret = ueye.is_GetFrameTimeRange(
                self.h_cam,
                mini, maxi, interv)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)
        return [float(1/maxi), float(1/mini)]

    def set_pixelclock(self, pixelclock) -> None:
        """
        Set the current pixelclock.
        Warning: when changing pixelclock at runtime, you may need to 
            update the fps and exposure parameters
        Params
        =======
        pixelclock: number
            Current pixelclock.
        """
        # get pixelclock range
        pcrange = (ueye.c_uint*3)()
        ret = ueye.is_PixelClock(self.h_cam, ueye.IS_PIXELCLOCK_CMD_GET_RANGE,
                                 pcrange, 12)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

        pcmin, pcmax, pcincr = pcrange
        if pixelclock < pcmin:
            pixelclock = pcmin
            print(f"Pixelclock out of range [{pcmin}, {pcmax}] and set "
                  f"to {pcmin}")
        elif pixelclock > pcmax:
            pixelclock = pcmax
            print(f"Pixelclock out of range [{pcmin}, {pcmax}] and set "
                  f"to {pcmax}")
        # Set pixelclock
        pixelclock = ueye.c_uint(pixelclock)
        ret = ueye.is_PixelClock(self.h_cam, ueye.IS_PIXELCLOCK_CMD_SET,
                                 pixelclock, 4)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

    def get_pixelclock(self) -> int:
        """
        Get the current pixelclock.
        Returns
        =======
        pixelclock: number
            Current pixelclock.
        """
        pixelclock = ueye.c_uint()
        ret = ueye.is_PixelClock(self.h_cam, ueye.IS_PIXELCLOCK_CMD_GET,
                                 pixelclock, 4)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)
        return pixelclock

    def set_exposure(self, exposure: float) -> None:
        """
        Set the exposure.
        Returns
        =======
        exposure: number
            Real exposure, can be slightly different than the asked one.
        """
        new_exposure = ueye.c_double(exposure)
        ret = ueye.is_Exposure(self.h_cam,
                               ueye.IS_EXPOSURE_CMD_SET_EXPOSURE,
                               new_exposure, 8)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

    def get_exposure(self) -> float:
        """
        Get the current exposure.
        Returns
        =======
        exposure: number
            Current exposure.
        """
        exposure = ueye.c_double()
        ret = ueye.is_Exposure(self.h_cam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE,
                               exposure,  8)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

        return exposure

    def set_exposure_auto(self, toggle):
        """
        Set auto expose to on/off.
        Params
        =======
        toggle: integer
            1 activate the auto gain, 0 deactivate it
        """
        value = ueye.c_double(toggle)
        value_to_return = ueye.c_double()
        ret = ueye.is_SetAutoParameter(self.h_cam,
                                       ueye.IS_SET_ENABLE_AUTO_SHUTTER,
                                       value,
                                       value_to_return)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

    def set_gain_auto(self, toggle):
        """
        Set/unset auto gain.
        Params
        ======
        toggle: integer
            1 activate the auto gain, 0 deactivate it
        """
        value = ueye.c_double(toggle)
        value_to_return = ueye.c_double()
        ret = ueye.is_SetAutoParameter(self.h_cam,
                                       ueye.IS_SET_ENABLE_AUTO_GAIN,
                                       value,
                                       value_to_return)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

    def __get_timeout(self):
        fps = self.get_fps()
        if fps == 0:
            fps = 1
        return int(1.5*(1/fps)+1)*1000

    def capture_video(self, wait=False):
        """
        Begin capturing a video.
        Parameters
        ==========
        wait: boolean
           To wait or not for the camera frames (default to False).
        """
        self.alloc()
        wait_param = ueye.IS_WAIT if wait else ueye.IS_DONT_WAIT
        return ueye.is_CaptureVideo(self.h_cam, wait_param)

    def stop_video(self):
        """
        Stop capturing the video.
        """
        return ueye.is_StopLiveVideo(self.h_cam, ueye.IS_FORCE_VIDEO_STOP)

    def capture_image(self, timeout=None):
        if timeout is None:
            timeout = self.__get_timeout()
        self.capture_video()
        img_buffer = ImageBuffer()
        ret = ueye.is_WaitForNextImage(self.camera,
                                       timeout,
                                       img_buffer.mem_ptr,
                                       img_buffer.mem_id)
        if ret == ueye.IS_SUCCESS:
            imdata = ImageData(self.camera, img_buffer)
            data = imdata.as_np_image()
            imdata.unlock()
            self.stop_video()
        else:
            data = None
        return data

    def capture_images(self, nmb, timeout=None):
        if timeout is None:
            timeout = self.__get_timeout()
        self.capture_video()
        ims = []
        for i in range(nmb):
            img_buffer = ImageBuffer()
            ret = ueye.is_WaitForNextImage(self.camera,
                                           timeout,
                                           img_buffer.mem_ptr,
                                           img_buffer.mem_id)
            if ret == ueye.IS_SUCCESS:
                imdata = ImageData(self.camera, img_buffer)
                ims.append(imdata.array)
                imdata.unlock()
            else:
                print(f"Warning: Missed {i}th frame !")
                ims.append(None)
        self.stop_video()
        return ims

    def freeze_video(self, wait=False):
        """
        Freeze the video capturing.
        Parameters
        ==========
        wait: boolean
           To wait or not for the camera frames (default to False).
        """
        wait_param = ueye.IS_WAIT if wait else ueye.IS_DONT_WAIT
        return ueye.is_FreezeVideo(self.h_cam, wait_param)

    def set_colormode(self, colormode):
        """
        Set the colormode.
        Parameters
        ==========
        colormode: pyueye color mode
            Colormode, as 'pyueye.IS_CM_BGR8_PACKED' for example.
        """
        ret = ueye.is_SetColorMode(self.h_cam, colormode)
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

    def get_colormode(self):
        """
        Get the current colormode.
        """
        ret = ueye.is_SetColorMode(self.h_cam, ueye.IS_GET_COLOR_MODE)
        return ret

    def get_format_list(self):
        """
        """
        count = ueye.UINT()
        ret = ueye.is_ImageFormat(self.h_cam, ueye.IMGFRMT_CMD_GET_NUM_ENTRIES,
                                  count, ueye.sizeof(count))
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)

        format_list = ueye.IMAGE_FORMAT_LIST(ueye.IMAGE_FORMAT_INFO *
                                             count.value)
        format_list.nSizeOfListEntry = ueye.sizeof(ueye.IMAGE_FORMAT_INFO)
        format_list.nNumListElements = count.value
        ret = ueye.is_ImageFormat(self.h_cam, ueye.IMGFRMT_CMD_GET_LIST,
                                  format_list, ueye.sizeof(format_list))
        if ret != ueye.IS_SUCCESS:
            raise UEyeError(ret)
        return format_list