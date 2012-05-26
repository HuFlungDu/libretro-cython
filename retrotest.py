from retro import core, exceptions

def video_refresh_cb(data,width,height,pitch):
	print "video refresh"
def audio_sample_cb(left,right):
	print "audio sample"
def input_poll_cb():
	print "input poll"
def input_state_cb(port, device, index, id):
	print "input state"
	return False

system = core.EmulatedSystem("./libretro-fceu.so")
system.set_video_refresh_cb(video_refresh_cb)
system.set_audio_sample_cb(audio_sample_cb)
system.set_input_poll_cb(input_poll_cb)
system.set_input_state_cb(input_state_cb)
print system.get_library_info().library_name
with open("Contra.nes", "r") as gamefile:
	gamedata = gamefile.read()
#if len(gamedata)%0x8000:
#	gamedata = gamedata[0x200:]
system.load_game_normal(gamedata,path="/home/huflungdu/libretro-cython/Contra.nes")
