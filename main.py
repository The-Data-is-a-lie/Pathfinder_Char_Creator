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
				if random.randint(1, 1000) == 1000:
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


