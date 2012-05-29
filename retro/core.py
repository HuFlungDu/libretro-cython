"""
A Pythonic interface to libretro functionality.

Each emulated console is represented by an instance of the EmulatedSystem class. For
technical reasons, a single copy of a libretro library can only emulate a single
system, therefore if you want to emulate multiple consoles from the same Python
process, you will need multiple copies of libretro.

To construct an EmulatedSystem object, you need to pass the name of the libretro
implementation to load. Different platforms use different default libretro
filenames, so if you don't have a particular one in mind, you should try the
names suggested by guess_library_name().

Constants defined in this module:

        MEMORY_* constants represent the diffent types of non-volatile storage
        a libretro game can use. Not every game uses every kind of storage,
        some games use no storage at all. These constants are useful for
        indexing into the list returned from EmulatedSystem.unload().

        VALID_MEMORY_TYPES is a list of all the valid memory type constants.

        DEVICE_* (but not DEVICE_ID_*) constants represent the different kinds of
        controllers that can be connected to a port. These should be passed to
        EmulatedSystem.set_controller_port_device() and will be given to the callback
        passed to EmulatedSystem.set_input_state_cb().

        DEVICE_ID_* constants represent the button and axis inputs on various
        controllers. They will be given to the callback passed to
        EmulatedSystem.set_input_state_cb().

Based on screwtape's python-snes.
"""

import numpy

from retro import _retro_wrapper as W
from retro import exceptions as EX
from retro.globals import *

# Since a dynamic library can only be loaded once per process, we need to keep
# track of which libraries have been loaded so we don't try and load them
# twice.
_libretro_registry = set()

def guess_library_name(tag=None):
        """
        Yield possible names of the libretro library.

        If tag is None or not supplied, names will be platform-appropriate
        variants of "retro" (such as "libretro.so"), otherwise they will be
        platform-appropriate variants of "retro-%(tag)s" (such as
        "libretro-tagname.so").

        None of the guessed names are guaranteed to exist on any particular
        platform or installation.
        """
        if tag is None:
                tag = ""
        else:
                tag = "-" + tag

        for pattern in ["libretro%s.so", "libretro%s.dylib",
                        "retro%s.dll"]:
                yield pattern % tag

class EmulatedSystem(W.LowLevelWrapper):
        """
        Represents a single emulated console, implemented by a libretro library.

        Once constructed, typical usage goes like this:

                1. Call the set_*_cb methods to set up the callbacks that will be
                   notified when the emulated console has produced a video frame, audio
                   sample, or needs controller input.
                2. Call one of the load_game_* methods to give the emulated console
                   a game image to run.
                3. Call set_controller_port_device() to connect appropriate controllers
                   to the emulated console.
                4. Call get_refresh_rate() to determine the intended refresh rate of
                   the loaded game.
                5. Call run() to cause emulation to occur. Process the output and
                   supply input as the registered callbacks are called. For real-time
                   playback, call run() at the refresh rate returned by
                   get_refresh_rate().
                6. Call unload() to free the resources associated with the loaded
                   game, and return the contents of the game's non-volatile
                   storage for use with the next session.
                7. If you want to switch to a different game, call
                   a load_game_* method again, and go to step 3.
        """
        # This keeps track of whether a game is loaded.
        _game_loaded = False

        # This keeps track of which cheats the user wants to apply to this game.
        _loaded_cheats = {}

        def __init__(self, libname):
                """
                Construct and return a wrapper for the given libretro library.

                "libname" should be the platform appropriate filename of the libretro
                implementation to load. If you don't have a specific filename you want
                to load, ask guess_library_name() for some likely choices.

                Raises LibraryInUse if the given library is already being used in the
                current process.
                """
                if libname in _libretro_registry:
                        raise EX.LibraryInUse("Library %r already in use." % (libname,))
                W.LowLevelWrapper.__init__(self, libname)
                _libretro_registry.add(libname)

                # libretro likes to segfault if you call .run without any callbacks set,
                # so let's define some dummy ones by default.
                self.set_video_refresh_cb(lambda *args: None)
                self.set_audio_sample_cb(lambda *args: None)
                self.set_input_poll_cb(lambda: None)
                self.set_input_state_cb(lambda *args: 0)

        def _reload_cheats(self):
                """
                Internal method.

                Reloads cheats in the emulated console from the _loaded_cheats variable.
                """
                self._lib.retro_cheat_reset()

                for index, (code, enabled) in self._loaded_cheats.items():
                        self._lib.retro_cheat_set(index, enabled, code)

        def _memory_to_string(self, mem_type):
                """
                Internal method.

                Copies data from the given libretro memory buffer into a numpy array.
                """
                mem_size = self._lib.retro_get_memory_size(mem_type)
                mem_data = self._lib.retro_get_memory_data(mem_type)

                if mem_size == 0:
                        return None

                return mem_data.tostring()

        def _string_to_memory(self, data, mem_type):
                """
                Internal method.

                Copies the given data into the libretro memory buffer of the given type.
                """
                mem_size = self._lib.retro_get_memory_size(mem_type)
                mem_data = self._lib.retro_get_memory_data(mem_type)

                if len(data) != mem_size:
                        raise EX.RetroException("This game requires %d bytes of "
                                        "memory type %d, not %d bytes" % (
                                                mem_size, mem_type, len(data),
                                        )
                                )
                mem_data.put(range(mem_size),map(ord,data))

        def _require_game_loaded(self):
                """
                Raise an exception if a game is not loaded.
                """
                if not self._game_loaded:
                        raise EX.NoGameLoaded("This method requires that a game be loaded!")

        def _require_game_not_loaded(self):
                """
                Raise an exception if a game is already loaded.
                """
                if self._game_loaded:
                        raise EX.GameAlreadyLoaded("This method requires that no game be loaded!")

        # Python wrapper functions that handle all the ctypes callback casting.
        def set_environment_cb(self,callback):
                """
                Sets the environment callback.

                Environment callback. Gives implementations a way of performing uncommon tasks. Extensible.

                The callback should accept the following parameters:

                        "command" is an int16 that tells it what command to use, one of globals.ENVIRONMENT_*.

                        "data" is an object which the implementation will create based on the value of "command"

                The callback should return nothing.

                The "data" pararmeter is currently unimplemented and just returns a wrapper around a void *
                """
                self._lib.retro_set_environment(callback)

        def set_video_refresh_cb(self, callback):
                """
                Sets the callback that will handle updated video frames.

                The callback should accept the following parameters:

                        "data" is a pointer to the top-left of an array of pixels.

                        "width" is the number of pixels in each row of the frame.

                        "height" is the number of pixel-rows in the frame.

                        "pitch" is the number of pixels from the beginning of one line to
                        the beginning of the text.

                The callback should return nothing.
                """
                self._lib.retro_set_video_refresh(callback)

        def set_audio_sample_cb(self, callback):
                """
                Sets the callback that will handle updated audio frames.

                The callback should accept the following parameters:

                        "left" is an int16 that specifies the left audio channel volume.

                        "right" is an int16 that specifies the right audio channel volume.

                The callback should return nothing.
                """
                self._lib.retro_set_audio_sample(callback)

        def set_audio_sample_batch_cb(self,callback):
                """
                Sets the callback that will handle updated batch audio frames.

                The callback should accept the following parameters:

                        "data" is an array of int16 pairs arranged in the format [l,r,l,r,...]

                        "frames" is the number of frames. The size of data is 2*frames

                The callback should return nothing.
                """
                self._lib.retro_set_audio_sample_batch(callback)

        def set_input_poll_cb(self, callback):
                """
                Sets the callback that will check for updated input events.

                The callback should accept no parameters and return nothing. It should
                just read new input events and store them somewhere so they can be
                returned by the input state callback.
                """
                self._lib.retro_set_input_poll(callback)

        def set_input_state_cb(self, callback):
                """
                Sets the callback that reports the current state of input devices.

                The callback may be called multiple times per frame with the same
                parameters.

                The callback will not be called if the loaded game does not try to
                probe the controllers.

                The callback will not be called for a particular port if DEVICE_NONE is
                connected to it.

                The callback should accept the following parameters:

                        "port" is an int describing which controller port is being reported.

                        "device" is one of the DEVICE_* constants describing which type of
                        device is currently connected to the given port.

                        "index" is a number describing which of the devices connected to
                        the port is being reported. It's only useful for
                        DEVICE_JOYPAD_MULTITAP - for other device types, it's always 0.

                        "id" is one of the DEVICE_ID_* constants for the given device,
                        describing which button or axis is being reported (for
                        DEVICE_JOYPAD_MULTITAP, use the DEVICE_ID_JOYPAD_* IDs).

                If "id" represents an analogue input (such as DEVICE_ID_MOUSE_X and
                DEVICE_ID_MOUSE_Y), you should return a value between -32768 and 32767.
                If it represents a digital input such as DEVICE_ID_MOUSE_LEFT or
                DEVICE_ID_MOUSE_RIGHT), return 1 if the button is pressed, and
                0 otherwise.

                If "id" represents an unknown input (one without a matching DEVICE_ID_*
                constant), return 0.

                You are responsible for implementing any turbo-fire features, etc.
                """
                self._lib.retro_set_input_state(callback)

        def set_controller_port_device(self, port, device):
                """
                Connects the given device to the given controller port.

                Connecting a device to a port implicitly removes any device previously
                connected to that port. To remove a device without connecting a new
                one, pass DEVICE_NONE as the device parameter. From this point onward,
                the callback passed to set_input_state_cb() will be called with the
                appropriate device, index and id parameters.

                Whenever you call a load_game_* function a DEVICE_JOYPAD will be
                connected to both ports, and devices previously connected using this
                function will be disconnected.

                It's generally safe (that is, it won't crash or segfault) to call this
                function any time, but for sensible operation, don't call it from
                inside the registered input state callback.

                "port" must be an integer describing which port the given controller
                will be connected to. If "port" is set to 1, the "device" parameter
                should not be DEVICE_LIGHTGUN_SUPER_SCOPE, DEVICE_LIGHTGUN_JUSTIFIER or
                DEVICE_LIGHTGUN_JUSTIFIERS.

                "device" must be one of the DEVICE_* (but not DEVICE_ID_*) constants,
                describing what kind of device will be connected to the given port.
                The devices are:

                        - DEVICE_NONE: No device is connected to this port. The registered
                          input state callback will not be called for this port.
                        - DEVICE_JOYPAD: A standard SNES-like gamepad.
                        - DEVICE_MOUSE: A mouse.
                        - DEVICE_KEYBOARD: A keyboard.
                        - DEVICE_LIGHTGUN: A light-gun.
                        - DEVICE_JOYPAD_MULTITAP: A multitap controller, which acts like
                          4 DEVICE_JOYPADs. Your input state callback will be passed "id"
                          parameters between 0 and 3.
                        - DEVICE_LIGHTGUN_SUPER_SCOPE: A Nintendo Super Scope light-gun
                          device (only works properly in port 2).
                        - DEVICE_LIGHTGUN_JUSTIFIER: A Konami Justifier light-gun device
                          (only works properly in port 2).
                        - DEVICE_LIGHTGUN_JUSTIFIERS: Two Konami Justifier light-gun
                          devices, daisy-chained together (only works properly in port 2).
                          Your input state callback will be passed "id" parameters 0 and 1.
                """
                self._lib.retro_set_controller_port_device(port, device)


        def reset(self):
                """
                Press the reset button on the emulated console.

                Requires that a game be loaded.
                """
                self._require_game_loaded()
                self._lib.retro_reset()

        def run(self):
                """
                Run the emulated console for one frame.

                Before this function returns, the registered callbacks will be called
                at least once each.

                This function should be called fifty (for PAL game) or sixty (for
                NTSC games) times per second for real-time emulation.

                Requires that a game be loaded.
                """
                self._require_game_loaded()
                self._lib.retro_run()

        def unload(self):
                """
                Remove the game and return its non-volatile storage contents.

                Returns a list with an entry for each MEMORY_* constant in
                VALID_MEMORY_TYPES. If the current game uses that type of storage,
                the corresponding index in the list will be a string containing the
                storage contents, which can later be passed to load_game_*.
                Otherwise, the corresponding index is None.

                Requires that a game be loaded.
                """
                self._require_game_loaded()

                res = [self._memory_to_string(t) for t in VALID_MEMORY_TYPES]
                self._lib.retro_unload_game()
                self._loaded_cheats = {}
                self._game_loaded = False
                return res

        def get_refresh_rate(self):
                """
                Return the intended refresh-rate of the loaded game.
                """
                av_info = self._lib.retro_get_system_av_info()
                return av_info.timing.fps

        def serialize(self):
                """
                Serializes the state of the emulated console to a string.

                This serialized data can be handed to unserialize() at a later time to
                resume emulation from this point.

                Requires that a game be loaded.
                """
                self._require_game_loaded()
                size = self._lib.retro_serialize_size()
                buf = ctypes.create_string_buffer(size)
                buf = numpy.empty(size, numpy.dtype("b"))
                res = self._lib.retro_serialize(buf, size)
                if not res:
                        raise EX.RetroException("problem in serialize")
                return buf

        def get_save_data(self):
                return self._memory_to_string(MEMORY_SAVE_RAM)

        def unserialize(self, state):
                """
                Restores the state of the emulated console from a string.

                Note that the game's SRAM data is part of the saved state.

                Requires that the same game that was loaded when serialize was
                called, be loaded before unserialize is called.
                """
                res = self._lib.retro_unserialize(state,
                                len(state))
                if not res:
                        raise EX.RetroException("problem in unserialize")

        def cheat_add(self, index, code, enabled=True):
                """
                Stores the given cheat code at the given index in the cheat list.

                "index" must be an integer. Only one cheat can be stored at any given
                index.

                "code" must be a string containing a valid Game Genie cheat code, or
                a sequence of them separated with plus signs like
                "DD62-3B1F+DD12-FA2C".

                "enabled" must be a boolean. It determines whether the cheat code is
                enabled or not.
                """
                self._loaded_cheats[index] = (code, enabled)
                self._reload_cheats()

        def cheat_remove(self, index):
                """
                Removes the cheat at the given index from the cheat list.

                "index" must be an integer previously passed to cheat_add.
                """
                del self._loaded_cheats[index]
                self._reload_cheats()

        def cheat_set_enabled(self, index, enabled):
                """
                Enables or disables the cheat at the given index in the cheat list.

                "index" must be an integer previously passed to cheat_add.

                "enabled" must be a boolean. It determines whether the cheat code is
                enabled or not.
                """
                code, _ = self._loaded_cheats[index]
                self._loaded_cheats[index] = (code, enabled)
                self._reload_cheats()

        def cheat_is_enabled(self, index):
                """
                Returns true if the cheat at the given index is enabled.

                "index" must be an integer previously passed to cheat_add.
                """
                _, enabled = self._loaded_cheats[index]
                return enabled

        def load_game_normal(self, data="", sram=None, rtc=None, path="", meta=""):
                """
                Load an ordinary game into the emulated console.

                "data" must be a string containing the uncompressed, de-interleaved,
                headerless game image.

                "path" should be a string containing the file path to the game.

                "sram" should be a string containing the SRAM data saved from the
                previous session. If not supplied or None, the game will be given
                a fresh, blank SRAM region (some games don't use SRAM).

                "rtc" should be a string containing the real-time-clock data saved from
                the previous session. If not supplied or None, the game will be
                given a fresh, blank RTC region (most games don't use an RTC).
                """
                self._require_game_not_loaded()
                sysinfo = self._lib.retro_get_system_info()
                if sysinfo.need_fullpath and not path:
                        raise EX.FullPathRequired("Full path required but not given")
                if not (path or data):
                        raise EX.DataAndPathNotProvided("No ROM data or path provided")
                gameinfo = retro_game_info(path,
                                           data,
                                           len(data),
                                           meta)

                self._lib.retro_load_game(gameinfo)

                self._game_loaded = True

                if sram is not None:
                        self._string_to_memory(sram, MEMORY_SAVE_RAM)

                if rtc is not None:
                        self._string_to_memory(rtc, MEMORY_RTC)

        def get_library_info(self):
                """
                Return the name and version numbers (major, minor) of the library.
                """
                return self._lib.retro_get_system_info()

        def close(self):
                """
                Release all resources associated with this library instance.
                """
                if W:
                        W.LowLevelWrapper.close(self)
                        if self._libname in _libretro_registry:
                                _libretro_registry.remove(self._libname)