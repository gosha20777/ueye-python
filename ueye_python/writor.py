from pyueye import ueye
from threading import Thread
from .camera import Camera
from .image_buffer import ImageBuffer
from .image_data import ImageData
import os
import cv2


class CliWritor:
    def __init__(
        self, 
        camera: Camera,
        save_dir: str,
        save_format: str = 'jpg'
    ) -> None:
        self.cam = camera
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
        

    def write(self) -> None:
        self.cam.capture_video()
        img_buffer = ImageBuffer()
        while True:
            if self.idx % self.copacity == 0:
                print(f'Saved {self.idx} frames')
                self.dir_idx += 1
                self.save_dir = os.path.join(self.base_dir, str(self.dir_idx))
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
                save_path = os.path.join(
                    self.save_dir, 
                    str(self.idx) + '.' + self.save_format
                )
                cv2.imwrite(save_path, img)
                self.idx += 1
            else:
                print(f'Frame dropped')
    
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