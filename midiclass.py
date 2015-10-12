import re
import sys

from midiutil.MidiFile import MIDIFile

import parameter as p
import pygame
import pygame.midi

#================================================================#
# Helper function
#================================================================#
def note_to_pitch(note):
  """
  " Convert note name to pitch number in MIDI note list.
  """

  if '#' in note:
    n = 2
  else:
    n = 1
  ntp = (int(note[n:])+1)*12 + p.NOTE_NAME.index(note[0:n])

  return ntp

def numnote_resolve(numnote):
  pitch_str = re.search(r'[0-7][#b]?', numnote).group(0)
  print 'pitch_str:', pitch_str
  if pitch_str == '0':
    pitch = 999
  else:
    pitch = p.NUM_NOTE.index(pitch_str)

    ud_obj = re.search(r'[ud]+', numnote)
    # print 'ud_obj:', ud_obj
    if ud_obj:
      ud_str = ud_obj.group(0)
      if ud_str[0] == 'u':
        pitch += 12*len(ud_str)
      elif ud_str[0] == 'd':
        pitch -= 12*len(ud_str)
  #===== Get the beat =====#
  beat = 1.
  ## if there are brackets, use the equation inside to calculate the beat value ##
  beat_obj = re.search(r'\((.*)\)', numnote)
  if beat_obj:
    beat_str = beat_obj.group(0)
    beat = eval(beat_str)
  ## if there are no bracket, use the normal method to get the beat value ##
  else:
    beat_obj = re.search(r'[-+]+', numnote)
    if beat_obj:
      beat_str = beat_obj.group(0)
      if beat_str[0] == '-':
        beat = 0.5**len(beat_str)
      elif beat_str[0] == '+':
        beat = 2.**len(beat_str)

    beat_long_obj = re.search(r'\.+', numnote)
    if beat_long_obj:
      beat += beat/2.

  return (pitch, beat)

def play_midi(music_file):
    """
    " stream music with mixer.music module in blocking manner
    " this will stream the sound from disk while playing
    """
    #===== Initiate mixer =====#
    freq = 44100    # audio CD quality
    bitsize = -16   # unsigned 16 bit
    channels = 2    # 1 is mono, 2 is stereo
    buffer = 1024   # number of samples

    pygame.mixer.init(freq, bitsize, channels, buffer)
    pygame.mixer.music.set_volume(1.0)

    clock = pygame.time.Clock()
    try:
        pygame.mixer.music.load(music_file)
        # print "Music file %s loaded!" % music_file
    except pygame.error:
        print "File %s not found! (%s)" % (music_file, pygame.get_error())
        return
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        # check if playback has finished
        clock.tick(30)


#================================================================#
# MIDI class
#================================================================#
class MidiWorld():
  """
  " Define MIDI class
  "
  " 1. read numbered notation file, the notation file should follow the format shown below
  " 2. write MIDI file
  """
  def __init__(self, note_file):
    self.volume = 100
    self.channel = 0
    self.note_file = note_file
    self.set_note_list()
    self.set_track_info()
    #===== Initiate MIDI file object with n_track tracks =====#
    self.mf = MIDIFile(self.n_track)
    # mf.addTrackName(track, time, "Sample Track")


  def set_note_list(self):
    #===== Get note list from the notation file =====#
    with open(self.note_file) as nf:
      note_str = nf.read().replace('\n', ' ')

    self.note_list = re.split('\s+', note_str)


  def set_track_info(self):
    #===== Set number of tracks and their time =====#
    ## number of tracks or channels, here we set the two numbers the same
    self.n_track = int(self.note_list[0])
    ## set time for each track
    self.track_time = [0]*self.n_track
    ## set track program
    self.program = [int(x) for x in self.note_list[1:self.n_track+1]]

    #===== Get tracks, the track section is contained within {} =====#
    ## Get track sections
    self.ltc_ind = [i for i, x in enumerate(self.note_list) if x == '{']
    self.rtc_ind = [i for i, x in enumerate(self.note_list) if x == '}']
    if len(self.ltc_ind) != len(self.rtc_ind):
      print '{ and } should be pair matched.'
      sys.exit()
    ## Get tracks
    self.track = [[] for x in range(self.n_track)]

    for lind, rind in zip(self.ltc_ind, self.rtc_ind):
      track_number = int(self.note_list[lind-1])
      self.track[track_number] += self.note_list[lind+1:rind]

    ## Get the total number of track sections
    # self.n_track_section = len(self.ltc_ind)
    ## Get every track number from the track sections,
    ## len(track_number_list) = n_track
    # self.track_number_list = list()
    # for i in range(self.n_track_section):
    #   self.track_number_list.append(int(self.note_list[self.ltc_ind[i]-2]))


  def write_track(self, track_number):
    """
    " write to track and channel
    """
    #===== Get the track list =====#
    track = self.track[track_number]

    channel_number = track_number

    #===== Set program (instrument) for the channel =====#
    self.mf.addProgramChange(track_number, channel_number, self.track_time[track_number], self.program[track_number])

    #===== Find every piece contained by paired [] =====#
    lp_ind = [i for i, x in enumerate(track) if x == '[']
    rp_ind = [i for i, x in enumerate(track) if x == ']']
    if len(lp_ind) != len(rp_ind):
      print '[ and ] should be pair matched.'
      sys.exit()

    for p in range(len(lp_ind)):
      #===== Tempo and major symbol are before the '[' =====#
      tempo = int(track[lp_ind[p]-2])
      self.mf.addTempo(track_number, self.track_time[track_number], tempo)

      major = track[lp_ind[p]-1]
      major_pitch = note_to_pitch(major)

      #===== Resolve every note =====#
      for s in track[lp_ind[p]+1:rp_ind[p]]:
        pitch, beat = numnote_resolve(s)
        if pitch != 999:  # if it is not break note (0)
          self.mf.addNote(track_number, channel_number,
                          major_pitch+pitch, self.track_time[track_number], beat, self.volume)

        self.track_time[track_number] += beat

  def write_midifile(self, output_midi_file):
    #===== write to each channel =====#
    for itc in range(self.n_track):
      print 'itc:', itc
      self.write_track(itc)

    #===== write it to disk =====#
    with open(output_midi_file, 'wb') as outf:
      self.mf.writeFile(outf)
