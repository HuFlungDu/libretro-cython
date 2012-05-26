class RetroException(Exception):
	"""
	Something went wrong with libretro.
	"""

class NoGameLoaded(RetroException):
	"""
	Can't do this without a loaded cartridge.
	"""

class GameAlreadyLoaded(RetroException):
	"""
	Can't do this with a loaded cartridge.
	"""

class LibraryInUse(RetroException):
	"""
	The requested library is already being used by something else.
	"""

class LibraryVersionMismatch(RetroException):
	"""
	The library version is one we don't recognise.
	"""

class FullPathRequired(RetroException):
	"""
	Full path is required but not provided
	"""

class DataAndPathNotProvided(RetroException):
	"""
	Data and path are not provided
	"""

# backwards-compat.  TODO: see if this actually works in try-except blocks.
SNESException          = RetroException
NoCartridgeLoaded      = NoGameLoaded
CartridgeAlreadyLoaded = GameAlreadyLoaded

