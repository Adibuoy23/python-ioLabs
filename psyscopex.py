'''
module for handling USB boxes connected via psyscopex install, which circumcents the
usual HID driver.

we provide a HID "emulation" layer, so the rest of the code interacts with this in
the same way as for a HID device
'''

import logging

from ctypes import *

from hid import HIDDevice
from hid.cparser import parse, define

try:
    from hid.osx import IOObjectRelease, find_usb_devices, COMObjectRef, IOCreatePlugInInterfaceForService, \
                        CFUUIDGetConstantUUIDWithBytes, IOCFPlugInInterfaceStruct, SInt32, kIOCFPlugInInterfaceID, \
                        IUNKNOWN_C_GUTS, CFUUIDGetUUIDBytes
    on_osx=True
except:
    on_osx=False

kIOUSBDeviceClassName="IOUSBDevice"
kUSBVendorID="idVendor"
kUSBProductID="idProduct"

kIOUSBDeviceUserClientTypeID=CFUUIDGetConstantUUIDWithBytes(None,
    0x9d, 0xc7, 0xb7, 0x80, 0x9e, 0xc0, 0x11, 0xD4,
    0xa5, 0x4f, 0x00, 0x0a, 0x27, 0x05, 0x28, 0x61)

kIOUSBInterfaceUserClientTypeID=CFUUIDGetConstantUUIDWithBytes(None,
    0x2d, 0x97, 0x86, 0xc6, 0x9e, 0xf3, 0x11, 0xD4,
    0xad, 0x51, 0x00, 0x0a, 0x27, 0x05, 0x28, 0x61)

kIOUSBInterfaceInterfaceID=CFUUIDGetConstantUUIDWithBytes(None,
    0x73, 0xc9, 0x7a, 0xe8, 0x9e, 0xf3, 0x11, 0xD4,
    0xb1, 0xd0, 0x00, 0x0a, 0x27, 0x05, 0x28, 0x61)

kIOUSBDeviceInterfaceID=CFUUIDGetConstantUUIDWithBytes(None,
    0x5c, 0x81, 0x87, 0xd0, 0x9e, 0xf3, 0x11, 0xD4,
    0x8b, 0x45, 0x00, 0x0a, 0x27, 0x05, 0x28, 0x61)

define('USBDeviceAddress','UInt16')

class IOUSBDevRequest(Structure):
    _fields_=[
        parse('UInt8 bmRequestType').cstruct,
        parse('UInt8 bRequest').cstruct,
        parse('UInt16 wValue').cstruct,
        parse('UInt16 wIndex').cstruct,
        parse('UInt16 wLength').cstruct,
        parse('void *pData').cstruct,
        parse('UInt32 wLenDone').cstruct,
    ]

define('IOUSBDevRequest',IOUSBDevRequest)

IOAsyncCallback1=parse('void ( *IOAsyncCallback1)(void *refcon,IOReturn result,void *arg0)').ctype
define('IOAsyncCallback1',IOAsyncCallback1)

class IOUSBIsocFrame(Structure): 
    _fields_=[
        parse('IOReturn frStatus').cstruct,
        parse('UInt16 frReqCount').cstruct,
        parse('UInt16 frActCount').cstruct,
    ]

define('IOUSBIsocFrame',IOUSBIsocFrame)

class IOUSBDevRequestTO(Structure):
    _fields_=[
        parse('UInt8 bmRequestType').cstruct,
        parse('UInt8 bRequest').cstruct,
        parse('UInt16 wValue').cstruct,
        parse('UInt16 wIndex').cstruct,
        parse('UInt16 wLength').cstruct,
        parse('void *pData').cstruct,
        parse('UInt32 wLenDone').cstruct,
        parse('UInt32 noDataTimeout').cstruct,
        parse('UInt32 completionTimeout').cstruct,
    ]

define('IOUSBDevRequestTO', IOUSBDevRequestTO)

class IOUSBConfigurationDescriptor(Structure):
    _fields_=[
        parse('UInt8 bLength').cstruct,
        parse('UInt8 bDescriptorType').cstruct,
        parse('UInt16 wTotalLength').cstruct,
        parse('UInt8 bNumInterfaces').cstruct,
        parse('UInt8 bConfigurationValue').cstruct,
        parse('UInt8 iConfiguration').cstruct,
        parse('UInt8 bmAttributes').cstruct,
        parse('UInt8 MaxPower').cstruct,
    ]

define('IOUSBConfigurationDescriptor',IOUSBConfigurationDescriptor)
define('IOUSBConfigurationDescriptorPtr','IOUSBConfigurationDescriptor*')

class IOUSBFindInterfaceRequest(Structure):
    _fields_=[
        parse('UInt16 bInterfaceClass').cstruct,
        parse('UInt16 bInterfaceSubClass').cstruct,
        parse('UInt16 bInterfaceProtocol').cstruct,
        parse('UInt16 bAlternateSetting').cstruct,
    ]

define('IOUSBFindInterfaceRequest',IOUSBFindInterfaceRequest)

class IOUSBDeviceInterface(Structure):
    _fields_= IUNKNOWN_C_GUTS + \
    [
        parse('IOReturn (*CreateDeviceAsyncEventSource)(void *self, CFRunLoopSourceRef *source)').cstruct,
        parse('CFRunLoopSourceRef (*GetDeviceAsyncEventSource)(void *self)').cstruct,
        parse('IOReturn (*CreateDeviceAsyncPort)(void *self, mach_port_t *port)').cstruct,
        parse('mach_port_t (*GetDeviceAsyncPort)(void *self)').cstruct,
        parse('IOReturn (*USBDeviceOpen)(void *self)').cstruct,
        parse('IOReturn (*USBDeviceClose)(void *self)').cstruct,
        parse('IOReturn (*GetDeviceClass)(void *self, UInt8 *devClass)').cstruct,
        parse('IOReturn (*GetDeviceSubClass)(void *self, UInt8 *devSubClass)').cstruct,
        parse('IOReturn (*GetDeviceProtocol)(void *self, UInt8 *devProtocol)').cstruct,
        parse('IOReturn (*GetDeviceVendor)(void *self, UInt16 *devVendor)').cstruct,
        parse('IOReturn (*GetDeviceProduct)(void *self, UInt16 *devProduct)').cstruct,
        parse('IOReturn (*GetDeviceReleaseNumber)(void *self, UInt16 *devRelNum)').cstruct,
        parse('IOReturn (*GetDeviceAddress)(void *self, USBDeviceAddress *addr)').cstruct,
        parse('IOReturn (*GetDeviceBusPowerAvailable)(void *self, UInt32 *powerAvailable)').cstruct,
        parse('IOReturn (*GetDeviceSpeed)(void *self, UInt8 *devSpeed)').cstruct,
        parse('IOReturn (*GetNumberOfConfigurations)(void *self, UInt8 *numConfig)').cstruct,
        parse('IOReturn (*GetLocationID)(void *self, UInt32 *locationID)').cstruct,
        parse('IOReturn (*GetConfigurationDescriptorPtr)(void *self, UInt8 configIndex, IOUSBConfigurationDescriptorPtr *desc)').cstruct,
        parse('IOReturn (*GetConfiguration)(void *self, UInt8 *configNum)').cstruct,
        parse('IOReturn (*SetConfiguration)(void *self, UInt8 configNum)').cstruct,
        parse('IOReturn (*GetBusFrameNumber)(void *self, UInt64 *frame, AbsoluteTime *atTime)').cstruct,
        parse('IOReturn (*ResetDevice)(void *self)').cstruct,
        parse('IOReturn (*DeviceRequest)(void *self, IOUSBDevRequest *req)').cstruct,
        parse('IOReturn (*DeviceRequestAsync)(void *self, IOUSBDevRequest *req, IOAsyncCallback1 callback, void *refCon)').cstruct,
        parse('IOReturn (*CreateInterfaceIterator)(void *self, IOUSBFindInterfaceRequest *req, io_iterator_t *iter)').cstruct,
    ]
    
define('IOUSBDeviceInterface',IOUSBDeviceInterface)

class IOUSBInterfaceInterface182(Structure):
    _fields_ = IUNKNOWN_C_GUTS + \
    [
        parse('IOReturn (*CreateInterfaceAsyncEventSource)(void *self, CFRunLoopSourceRef *source)').cstruct,
        parse('CFRunLoopSourceRef (*GetInterfaceAsyncEventSource)(void *self)').cstruct,
        parse('IOReturn (*CreateInterfaceAsyncPort)(void *self, mach_port_t *port)').cstruct,
        parse('mach_port_t (*GetInterfaceAsyncPort)(void *self)').cstruct,
        parse('IOReturn (*USBInterfaceOpen)(void *self)').cstruct,
        parse('IOReturn (*USBInterfaceClose)(void *self)').cstruct,
        parse('IOReturn (*GetInterfaceClass)(void *self, UInt8 *intfClass)').cstruct,
        parse('IOReturn (*GetInterfaceSubClass)(void *self, UInt8 *intfSubClass)').cstruct,
        parse('IOReturn (*GetInterfaceProtocol)(void *self, UInt8 *intfProtocol)').cstruct,
        parse('IOReturn (*GetDeviceVendor)(void *self, UInt16 *devVendor)').cstruct,
        parse('IOReturn (*GetDeviceProduct)(void *self, UInt16 *devProduct)').cstruct,
        parse('IOReturn (*GetDeviceReleaseNumber)(void *self, UInt16 *devRelNum)').cstruct,
        parse('IOReturn (*GetConfigurationValue)(void *self, UInt8 *configVal)').cstruct,
        parse('IOReturn (*GetInterfaceNumber)(void *self, UInt8 *intfNumber)').cstruct,
        parse('IOReturn (*GetAlternateSetting)(void *self, UInt8 *intfAltSetting)').cstruct,
        parse('IOReturn (*GetNumEndpoints)(void *self, UInt8 *intfNumEndpoints)').cstruct,
        parse('IOReturn (*GetLocationID)(void *self, UInt32 *locationID)').cstruct,
        parse('IOReturn (*GetDevice)(void *self, io_service_t *device)').cstruct,
        parse('IOReturn (*SetAlternateInterface)(void *self, UInt8 alternateSetting)').cstruct,
        parse('IOReturn (*GetBusFrameNumber)(void *self, UInt64 *frame, AbsoluteTime *atTime)').cstruct,
        parse('IOReturn (*ControlRequest)(void *self, UInt8 pipeRef, IOUSBDevRequest *req)').cstruct,
        parse('IOReturn (*ControlRequestAsync)(void *self, UInt8 pipeRef, IOUSBDevRequest *req, IOAsyncCallback1 callback, void *refCon)').cstruct,
        parse('IOReturn (*GetPipeProperties)(void *self, UInt8 pipeRef, UInt8 *direction, UInt8 *number, UInt8 *transferType, UInt16 *maxPacketSize, UInt8 *interval)').cstruct,
        parse('IOReturn (*GetPipeStatus)(void *self, UInt8 pipeRef)').cstruct,
        parse('IOReturn (*AbortPipe)(void *self, UInt8 pipeRef)').cstruct,
        parse('IOReturn (*ResetPipe)(void *self, UInt8 pipeRef)').cstruct,
        parse('IOReturn (*ClearPipeStall)(void *self, UInt8 pipeRef)').cstruct,
        parse('IOReturn (*ReadPipe)(void *self, UInt8 pipeRef, void *buf, UInt32 *size)').cstruct,
        parse('IOReturn (*WritePipe)(void *self, UInt8 pipeRef, void *buf, UInt32 size)').cstruct,
        parse('IOReturn (*ReadPipeAsync)(void *self, UInt8 pipeRef, void *buf, UInt32 size, IOAsyncCallback1 callback, void *refcon)').cstruct,
        parse('IOReturn (*WritePipeAsync)(void *self, UInt8 pipeRef, void *buf, UInt32 size, IOAsyncCallback1 callback, void *refcon)').cstruct,
        parse('IOReturn (*ReadIsochPipeAsync)(void *self, UInt8 pipeRef, void *buf, UInt64 frameStart, UInt32 numFrames, IOUSBIsocFrame *frameList,'
                                      'IOAsyncCallback1 callback, void *refcon)').cstruct,
        parse('IOReturn (*WriteIsochPipeAsync)(void *self, UInt8 pipeRef, void *buf, UInt64 frameStart, UInt32 numFrames, IOUSBIsocFrame *frameList,'
                                      'IOAsyncCallback1 callback, void *refcon)').cstruct,
        parse('IOReturn (*ControlRequestTO)(void *self, UInt8 pipeRef, IOUSBDevRequestTO *req)').cstruct,
        parse('IOReturn (*ControlRequestAsyncTO)(void *self, UInt8 pipeRef, IOUSBDevRequestTO *req, IOAsyncCallback1 callback, void *refCon)').cstruct,
        parse('IOReturn (*ReadPipeTO)(void *self, UInt8 pipeRef, void *buf, UInt32 *size, UInt32 noDataTimeout, UInt32 completionTimeout)').cstruct,
        parse('IOReturn (*WritePipeTO)(void *self, UInt8 pipeRef, void *buf, UInt32 size, UInt32 noDataTimeout, UInt32 completionTimeout)').cstruct,
        parse('IOReturn (*ReadPipeAsyncTO)(void *self, UInt8 pipeRef, void *buf, UInt32 size, UInt32 noDataTimeout, UInt32 completionTimeout, IOAsyncCallback1 callback, void *refcon)').cstruct,
        parse('IOReturn (*WritePipeAsyncTO)(void *self, UInt8 pipeRef, void *buf, UInt32 size, UInt32 noDataTimeout, UInt32 completionTimeout, IOAsyncCallback1 callback, void *refcon)').cstruct,
        parse('IOReturn (*USBInterfaceGetStringIndex)(void *self, UInt8 *si)').cstruct,
    ]

def find_devices():
    # attempt to directly find usb devices via
    # this function from hid lib (fail gracefully if
    # we're not running on os x)
    if on_osx:
        return find_usb_devices(kIOUSBDeviceClassName,kUSBVendorID,kUSBProductID,PsyScopeXUSBDevice)
    return []

class PsyScopeXUSBDevice(HIDDevice):
    def __init__(self, dev, vendor, product):
        super(PsyScopeXUSBDevice,self).__init__(vendor,product)
        self._usbDevice=dev
        
        # cache these so they are guaranteed to be available
        # when calling __del__
        self.IOObjectRelease=IOObjectRelease
        self.logging_info=logging.info
        self._parent__del__=super(PsyScopeXUSBDevice,self).__del__
    
    def __del__(self):
        self._parent__del__()
        if self._usbDevice:
            self.logging_info("releasing USB device: %s"%self)
            self.IOObjectRelease(self._usbDevice)
    
    def open(self):
        logging.info("opening hid device via usb")
        # plugInInterface initialised to NULL
        plugInInterface=COMObjectRef(POINTER(POINTER(IOCFPlugInInterfaceStruct))())
        score=SInt32()
        err=IOCreatePlugInInterfaceForService(self._usbDevice, kIOUSBDeviceUserClientTypeID,
            kIOCFPlugInInterfaceID, byref(plugInInterface.ref), byref(score));
        
        print err
        
        # query to get the USB interface
        usbDevInterface=POINTER(POINTER(IOUSBDeviceInterface))()
        res=plugInInterface.QueryInterface(CFUUIDGetUUIDBytes(kIOUSBDeviceInterfaceID),parse('LPVOID*').cast(byref(usbDevInterface)))
        print res
        #self._hidInterface=COMObjectRef(hidInterface)
        
        # open the HID device
        #self._hidInterface.open(0)

if __name__ == '__main__':
    for dev in find_devices():
        print dev