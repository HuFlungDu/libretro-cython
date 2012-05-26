'''
A low-level cython wrapper for libretro API.

You probably want to use the Python API in retro.core instead of this.

Based on screwtape's python-snes module
'''

from _retro import CoreDef
from retro import exceptions as EX
from retro.globals import *

class LowLevelWrapper(object):
	_lib_active = False
	def __init__(self,libname):
		self._libname = libname
		self._lib = CoreDef(libname)
		self.api_version = self._lib.retro_api_version()
		if self.api_version != RETRO_API_VERSION:
			raise EX.LibraryVersionMismatch("Unsupported libretro API version "
					"{}".format(self.api_version)
				)

		self._lib.retro_init()
		self._lib_active = True

	def close(self):
		self._lib.retro_deinit()
		self._lib_active = False

	def __del__(self):
		if self._lib_active:
			self.close()