from pyueye import ueye
from threading import Thread
from .camera import Camera
from .image_buffer import ImageBuffer
from .image_data import ImageData
import os
import cv2
import numpy as np
from datetime import datetime
import hashlib


# nmb_frames = 3000
# filepath= "video1.avi"
# wait = input("PRESS ENTER TO BEGIN RECORDING.")
# cam.set_colormode(ueye.IS_CM_MONO8)
# # Create a thread to save a video
# thread = RecordThread(cam, path=filepath,
#                       use_memory=True,
#                       nmb_frame=nmb_frames,
#                       verbose=True)
# thread.start()
# # Wait for the thread to edn
# thread.join()


class GatherThread(Thread):
    def __init__(
            self, 
            camera: Camera, 
            copy=True):
        """
        Thread used for gather images.
        """
        super().__init__()
        self.timeout = 1000
        self.cam = camera
        self.running = True
        self.copy = copy

        self.cam.capture_video()

    def run(self):
        while self.running:
            img_buffer = ImageBuffer()
            ret = ueye.is_WaitForNextImage(self.cam,
                                           self.__get_timeout(),
                                           img_buffer.mem_ptr,
                                           img_buffer.mem_id)
            if ret == ueye.IS_SUCCESS:
                imdata = ImageData(self.cam, img_buffer)
                self._process(imdata)

    def process(self, image_data: ImageData):
        pass

    def _process(self, image_data: ImageData):
        self.process(image_data)
    
    def __get_timeout(self):
        fps = self.cam.get_fps()
        if fps == 0:
            fps = 1
        return int(1.5*(1/fps)+1)*1000

    def stop(self):
        self.cam.stop_video()
        self.running = False


class VieoWritor(GatherThread):
    def __init__(self, 
                camera: Camera, 
                path: str, 
                duration: int, 
                copy=True,
            ):
        """
        Thread used to record videos.
        """
        super().__init__(camera=camera, copy=copy)
        fps = int(self.cam.get_fps())
        self.nmb_frame = duration * fps
        self.ind_frame = 0
        self.path = path
        self.vw = self.open_video_writer()

    def open_video_writer(self):
        aoi = self.cam.get_aoi()
        fourcc = cv2.VideoWriter_fourcc("M", "P", "E", "G")
        return cv2.VideoWriter(self.path,
                               fourcc=fourcc,
                               fps=24,
                               frameSize=(aoi.width, aoi.height),
                               isColor=0)
    def process(self, imdata: ImageData):
        self.vw.write(imdata.as_np_image())
        self.ind_frame += 1
        if self.ind_frame >= self.nmb_frame:
            self.stop()

    def stop(self):
        self.vw.release()
        super().stop()


class CliWritor:
    def __init__(
        self, 
        camera: Camera,
        bg_image: np.ndarray,
        save_dir: str,
        save_format: str = 'jpg',
        copacity: int = 100000
    ) -> None:
        self.cam = camera
        self.idx = 1
        self.dir_idx = 1
        self.copacity = copacity
        self.base_dir = save_dir
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.save_dir = os.path.join(self.base_dir, self.current_date, str(self.dir_idx))
        self.save_format = save_format
        self.bg_image = bg_image

        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        if not os.path.exists(os.path.join(self.base_dir, self.current_date)):
            os.makedirs(os.path.join(self.base_dir, self.current_date))

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        

    def write(self) -> None:
        self.cam.capture_video()
        img_buffer = ImageBuffer()
        while True:
            if self.idx % self.copacity == 0:
                print(f'Processed {self.idx * self.dir_idx} frames')
                self.dir_idx += 1
                self.idx = 1

                if self.current_date != datetime.now().strftime('%Y-%m-%d'):
                    self.current_date = datetime.now().strftime('%Y-%m-%d')
                    print(f'New date: {self.current_date}')
                    self.dir_idx = 1

                self.save_dir = os.path.join(
                    self.base_dir, 
                    self.current_date, 
                    str(self.dir_idx)
                )
                
                if not os.path.exists(
                    os.path.join(self.base_dir, self.current_date)
                    ):
                    os.makedirs(
                        os.path.join(self.base_dir, 
                        self.current_date)
                    )
                
                if not os.path.exists(self.save_dir):
                    os.makedirs(self.save_dir)
            
            ret = ueye.is_WaitForNextImage(
                self.cam.camera,
                self.__get_timeout(),
                img_buffer.mem_ptr,
                img_buffer.mem_id
            )

            if ret == ueye.IS_SUCCESS:
                img_data = ImageData(self.cam.camera, img_buffer)
                img = img_data.as_np_image()
                img_data.unlock()
                
                if not self.__is_empty_image(img):
                    name = hashlib.md5(img).hexdigest()
                    save_path = os.path.join(
                        self.save_dir, 
                        str(name) + '.' + self.save_format
                    )
                    cv2.imwrite(save_path, img)
                    self.idx += 1

                if self.idx % self.copacity == 0:
                    save_path = os.path.join(
                        self.base_dir, 
                        'sample.' + self.save_format
                    )
                    cv2.imwrite(save_path, img)
            else:
                print(f'Frame dropped')
    
    def __is_empty_image(self, image):
        img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        bg = cv2.cvtColor(self.bg_image, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(img, bg)
        diff = cv2.threshold(diff, 0, 255, cv2.THRESH_OTSU)[1]
        diff = cv2.dilate(diff, None, iterations=32)
        diff = cv2.erode(diff, None, iterations=32)
        return cv2.countNonZero(diff) < 100 or img.var() < 100
    
    def __get_timeout(self):
        fps = self.cam.get_fps()
        if fps == 0:
            fps = 1
        return int(1.5*(1/fps)+1)*1000


class ThreadWritor(Thread):
    def __init__(
        self, 
        camera: Camera,
        save_dir: str,
        save_format: str = 'jpg'
    ) -> None:
        Thread.__init__(self)
        self.cam = camera
        self.is_running = True
        self.idx = 0
        self.dir_idx = 0
        self.copacity = 100000
        self.base_dir = save_dir
        self.save_dir = os.path.join(self.base_dir, str(self.dir_idx))
        self.save_format = save_format

        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        

    def run(self) -> None:
        self.cam.capture_video()
        img_buffer = ImageBuffer()
        while self.is_running:
            if self.idx % self.copacity == 0:
                self.dir_idx += 1
                self.save_dir = os.path.join(self.base_dir, str(self.dir_idx))
                if not os.path.exists(self.save_dir):
                    os.makedirs(self.save_dir)
            
            ret = ueye.is_WaitForNextImage(
                self.cam.camera,
                self.cam.__get_timeout(),
                img_buffer.mem_ptr,
                img_buffer.mem_id
            )

            if ret == ueye.IS_SUCCESS:
                img_data = ImageData(self.cam.camera, img_buffer)
                img = img_data.as_np_image()
                img_data.unlock()
                save_path = os.path.join(
                    self.save_dir, 
                    str(self.idx) + '.' + self.save_format
                )
                cv2.imwrite(save_path, img)
                self.idx += 1
            else:
                print(f'Frame dropped')

    def stop(self) -> None:
        self.is_running = False
        self.cam.stop_video()