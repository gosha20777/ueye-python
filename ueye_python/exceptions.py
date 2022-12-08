from pyueye import ueye


class UEyeError(Exception):
    """
    A class to handle errors from the ueye API.
    """
    def __init__(self, error_code):
        self.error_code = error_code
        self.error_codes = {
            ueye.IS_INVALID_EXPOSURE_TIME: "Invalid exposure time",
            ueye.IS_INVALID_CAMERA_HANDLE: "Invalid camera handle",
            ueye.IS_INVALID_MEMORY_POINTER: "Invalid memory pointer",
            ueye.IS_INVALID_PARAMETER: "Invalid parameter",
            ueye.IS_IO_REQUEST_FAILED: "IO request failed",
            ueye.IS_NO_ACTIVE_IMG_MEM: "No active IMG memory",
            ueye.IS_NO_USB20: "No USB2",
            ueye.IS_NO_SUCCESS: "No success",
            ueye.IS_NOT_CALIBRATED: "Not calibrated",
            ueye.IS_NOT_SUPPORTED: "Not supported",
            ueye.IS_OUT_OF_MEMORY: "Out of memory",
            ueye.IS_TIMED_OUT: "Timed out",
            ueye.IS_CANT_OPEN_DEVICE: "Cannot open device",
            ueye.IS_ALL_DEVICES_BUSY: "All device busy",
            ueye.IS_DEVICE_ALREADY_PAIRED: "Device already in use",
            ueye.IS_TRANSFER_ERROR: "Transfer error"
        }

    def __str__(self):
        if self.error_code in self.error_codes:
            return self.error_codes[self.error_code]
        else:
            return "Unknown error code: {}".format(self.error_code)
