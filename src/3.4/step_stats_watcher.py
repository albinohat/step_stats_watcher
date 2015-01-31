## step_stats_watcher.py
## Author: Daniel "Albinohat" Mercado
## This script parses through Stepmania's Stats.xml file and stores information in a text file to be displayed on a livestream.

## Standard Imports
import os, re, sys, threading, time

## Third-Party Imports
from bs4 import BeautifulSoup

## Global Variables - Lazy Mode

VERSION = "0.1.2b released 2015-01-30"

## Initialize a list to check that all the required attributes are present.
config_bools     = [0, 0, 0, 0, 0]

bool_config      = 0
bool_help        = 0
bool_stdout      = 0
bool_version     = 0
bool_change      = 0
bool_exit        = 0
bool_show        = 1
bool_diff        = 1

stats_refresh    = 0
diff_refresh     = 0

display_name     = ""

current_seconds  = ""
current_time     = ""
current_notes    = ""
current_songs    = ""

previous_seconds = ""
previous_notes   = ""
previous_songs   = ""

## WriteDiffThread - A thread which writes the diffs to the required files.
class WriteDiffThread(threading.Thread):
	## __init__ - Initializes the attributes of the WriteDiffThread instance.
	def __init__(self):
		threading.Thread.__init__(self)
		self.start()

	## run - This method calls the writeDiff method.
	def run(self):
		writeDiff()

## writeDiff - Writes the differences in rank, PP and accuracy to text files.	
def writeDiff():
	## Reset the change bool and text.
	change_text = "\n== Stats Change @ " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " =="	
	bool_change = 0

	## This file's text will display stat changes.
	try:
		output_diff_file = open(output_diff_path, "w+")
		
	except IOError:
		print("\n    Error: Unable to write to \"" + output_diff_path + ".\" Please ensure you have the rights to write there.")
		sys.exit()	

	## Write a blank line to the file.
	output_diff_file.write("\n")
	
	## Only compare if the previous values aren't empty and if a change has occurred.
	if (previous_seconds != "" and previous_notes != "" and previous_songs != ""):	
		
		new_seconds = current_seconds - previous_seconds
		## Change
		if (new_seconds > 0):
			if (bool_stdout == 1):
				change_text += "\n    Gameplay Time: +" + (time.strftime("%H:%M:%S", time.gmtime(float(new_seconds))))

			output_diff_file.write("+" + str(time.strftime("%H:%M:%S", time.gmtime(float(new_seconds)))) + "\n")
			bool_change = 1
			
		## No Change. 
		else:
			output_diff_file.write("\n")

		new_notes = current_notes - previous_notes
		if (new_notes > 0):
			if (bool_stdout == 1):
				change_text += "\n     Notes Tapped: +"  + str('{0:,}'.format(new_notes))
				
			output_diff_file.write("+" + str('{0:,}'.format(current_notes)) + "\n")
			bool_change = 1			

		## No Change. 
		else:
			output_diff_file.write("\n")

		new_songs = current_songs - previous_songs
		if (new_songs > 0):
			if (bool_stdout == 1):
				change_text += "\n     Songs Played: +"  + str(new_songs)
				
			output_diff_file.write("+" + str(new_songs) + "\n")
			bool_change = 1			

		## No Change. 
		else:
			output_diff_file.write("\n")

	if (bool_stdout == 1 and bool_change == 1):
		print(change_text)
	
	output_diff_file.close()
	
	## Sleep then clear and close the files.
	for i in range(int(diff_refresh) * 4):
		if (bool_exit == 1):
			return

		time.sleep(0.25)

	output_diff_file = open(output_diff_path, "w+")
	output_diff_file.write(" \n \n \n ")	
	output_diff_file.close()
	
		
## writeStats - Writes the player stats to a text file.
def writeStats():
	## Open the file displayed on stream, write to it and close it.
	## Line 1 - Username
	## Line 2 - Time Played
	## Line 3 - Notes Tapped
	## Line 4 - Songs Played

	try:
		output_stats_file = open(output_stats_path, "w+")

	except IOError:
		print("\n    Error: Unable to write to \"" + stream_file + ".\" Please ensure you have the rights to write there.")
		sys.exit()

	output_stats_file.write(str(display_name) + "\n")
	output_stats_file.write("Time: " + str(current_time) + "\n")
	output_stats_file.write("Notes: " + str('{0:,}'.format(current_notes)) + "\n")
	output_stats_file.write("Songs: " + str(current_songs) + "\n")
	output_stats_file.close()

## Validate # of CLA
if (len(sys.argv) < 2 or len(sys.argv) > 4):
	print("\n    Invalid Syntax. Use -h for help.")
	sys.exit()

else:
	## Parse through the CLA, ignoring [0] since it it is the filename.
	## bool_help set to 1 will cause the script to exit.
	for arg in sys.argv:
		temp = arg.lower()
		if (arg != sys.argv[0]):
			if (temp == "-h" or temp == "--help"):
				bool_help = 1
			elif (temp == "-v" or temp == "--version"):
				bool_version = 1
			elif (temp == "-s" or temp == "--stdout"):
				bool_stdout = 1
			elif (temp == "--no-diff"):
				bool_diff = 0
			elif (re.match("--?\w+", temp)):
				print("\n    Invalid Syntax. Use -h for help.")
				sys.exit()	

			else:
				if (os.path.isfile(arg)):
					## Normalize (possibly invalid) save_dir attribute to use /.
					try:
						config_file = open(arg, "r+")

					except IOError:
						print("\n    Error: Unable to open file: \"" + arg + "\"")
						sys.exit()						
					
					bool_config = 1
					
					## Massage paths to use '/'
					for line in config_file:
						line = line.strip()
						## Ignore header line.
						if (line == "[step_stats_watcher]"):
							continue
						
						## Massage paths to use '/'
						line = re.sub(r'\\\\|\\', r'/', line)
						
						## Parse the config file and assign the path variables.
						key, value = line.split("=", 1)
						
						if (key == "input_stats_path"):
							input_stats_path = value
							config_bools[0] = 1

						elif (key == "output_stats_path"):
							output_stats_path = value
							config_bools[1] = 1

						elif (key == "output_diff_path"):
							output_diff_path = value
							config_bools[2] = 1

						elif (key == "stats_refresh"):
							stats_refresh = value
							config_bools[3] = 1

						elif (key == "diff_refresh"):
							diff_refresh = value
							config_bools[4] = 1

						else:
							print("\n    Invalid attribute \"" + key + "\". Exiting...\n")
							sys.exit()

				else:
					print("\n    Error. Unable to open file \"" + arg + "\"")
					sys.exit()						

## Print out the help dialog.
if (bool_help == 1):
	print("\n    Usage: " + sys.argv[0] + " [options] config_file\n")
	print("    Options")
	print("        -h | --help - Prints out this help.")
	print("        -s | --stdout - Prints out stat changes to STDOUT.")
	print("        -v | --version - Prints out the version you are using.")
	print("        --no-diff - Changes in stats won't be updated in separate text files. Stat-only mode.")
	print("\nconfig_file - The INI file containing the settings for the script.")

## Print out the version.
if (bool_version == 1):
	## Put a line between help and version.
	print("\n    Version " + VERSION)

## Exit if either help or version was specified.
if (bool_help == 1 or bool_version == 1):
	sys.exit()

## Exit if there was no config file specified.
if (bool_config == 0):
	print("\n    Invalid Syntax. Use -h for help.")
	sys.exit()

## Exit if there are missing configuration entires.
for each in config_bools:
	if (each == 0):
		print("\n    Invalid configuration. At least one required attribute is missing. See the Step Stats Watcher wiki for more information.")
		sys.exit()	

## Exit if the stats_refresh is smaller than 10 seconds.
if (float(stats_refresh) < 10):
	print("\n    Invalid configuration. stats_refresh must be at least 10.")
	sys.exit()
	
## Exit if stats_refresh is smaller than diff_refresh.
if (float(stats_refresh) <= float(diff_refresh)):
	print("\n    Invalid configuration. diff_refresh must be smaller than stats_refresh.")
	sys.exit()	

		
print("\nStep Stats Watcher is running. Press CTRL+C to exit.")

bool_init_stats = 1

while(1):
	try:
		## Open the stats file and read in the contents and close it again.
		input_stats_file = open(input_stats_path, "r")
		stats_text = input_stats_file.read()
		input_stats_file.close()

		## Extract the stats of interest from the file.
		soup = BeautifulSoup(stats_text, "xml")
		
		display_name    = str(soup.DisplayName.contents[0])
		current_seconds = int(soup.TotalGameplaySeconds.contents[0])
		current_time    = time.strftime("%H:%M:%S", time.gmtime(float(current_seconds)))
		current_notes   = int(soup.TotalTapsAndHolds.contents[0]) + int(soup.TotalJumps.contents[0]) + int(soup.TotalHolds.contents[0]) + int(soup.TotalRolls.contents[0]) + int(soup.TotalMines.contents[0]) + int(soup.TotalHands.contents[0])
		current_songs   = int(soup.NumTotalSongsPlayed.contents[0])

		## Note the initial stats.
		if (bool_init_stats == 1):
			start_display = display_name
			start_seconds = current_seconds
			start_notes   = current_notes
			start_songs   = current_songs

			bool_init_stats = 0
		
		## Write the current stats to a text file.
		writeStats()

		## write the difference in stats to a text file if enabled.
		if (bool_diff == 1):
			WriteDiffThread()

		## Update every second since that's how often gameplay time updates.
		time.sleep(float(stats_refresh))

		## Fill in the previous values to compare.			
		previous_seconds = current_seconds
		previous_notes   = current_notes
		previous_songs   = current_songs
		
	except KeyboardInterrupt:
		print("\nCTRL+C Detected. Exiting...")
		
		if (bool_stdout == 1):
			print("\n== Session Summary ==")
			print("    Gameplay Time: " + str(time.strftime("%H:%M:%S", time.gmtime(float(current_seconds - start_seconds)))))
			print("     Notes Tapped: "  + str('{0:,}'.format(current_notes - start_notes)))
			print("     Songs Played: "  + str(current_songs - start_songs))

		## Signal to the child thread to exit.
		bool_exit = 1
		
		## Exit main.
		sys.exit()
