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
		#User selects the region to start from (if they want to)
		

		if isTrue:
			#end of region macro
			CreateNewCharacter(character_name)
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
				print('character is extremely lucky, make it a luck build rather than everything else ', file=f)				
			elif random.randint(1,100) == 10:
				print('you need to take negative luck feats as well as normal feats ')
				print('you need to take negative luck feats as well as normal feats ', file = f)
				
				

		else: 
			print('Exiting Character Generator...')
			break



										#notes
#make stat total toggles
#make race and region toggeable (e.g. user_input region('Sojoria') -> leads to more likely classes (lower likelihood for magic casers ...) 

#using a list of all regions, weight weapon groups

#implement weights per region to decide what weapon a character uses