#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import isBool, Roll_Level #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random

print(style.BOLD + f'Welcome to the D&D Random Character Generator ({version})' + style.END)

isTrue = True


while isTrue:
	character_name = random.randint(0,10000000)
	# write the location of where you want it to export here:
	filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{character_name}_character_sheet.txt"
	with open(filename, 'a') as f:
		print('===============================================================',file=f)
		userInput = input('Create a new character? (y/n): ').lower()
		isTrue = isBool(userInput)

		if isTrue:
			print('===============================================================', file=f)
			CreateNewCharacter(character_name)
			user_input = input("Do you want levels to be weighted lower (if n then they are weighted higher)? (y/n) ")
			Roll_Level(character_name)
				#need to devise a way to randomly pick good feats

			
			for i in range(1, 11):
				if random.randint(1, 10000) == 10000:
					print(f'Character is mythic {i}')
					for j in range(2, 11):
						roll = random.randint(1, 100)
						if roll >= 90:
							print(f'Character is mythic {j}')
						else:
							break
				else:
					print('didnt get mythic ')
					break			

			if random.randint(1,100) == 100:
				print('character is extremely lucky, make it a luck build rather than everything else ')
			elif random.randint(1,100) == 10:
				print('you need to take negative luck feats as well as normal feats ')

		else: 
			print('Exiting Character Generator...')
			break



										#notes
#make stat total toggles
#make race and region toggeable (e.g. user_input region('Sojoria') -> leads to more likely classes (lower likelihood for magic casers ...) 

#using a list of all regions, weight weapon groups

#npc levels
#Include a way to make it so we decide how many npc levels out of total level
#make it toggled randomly (an option to have npc classes)
#if they have npc levels make it a .75 chance to get npc levels per level

#If level <= 3 one feat on path of war, if level <= 7 two feats on path of war, if level <=11 3 feats on path of war

#FULL BAB get's like a 75% chance for path of war abilities (if not path of war)
#if they get it, then they auto use 3 feats when they can (assuming their levels)
#25% chance they get another chain as well (if they are full BAB)

#Mid BAB 50% chance for path of war abilities
#10% chance for another chain

#low bab 25% chance for path of war abilities
#Only chance to do it once

#implement weights per region to decide what weapon a character uses