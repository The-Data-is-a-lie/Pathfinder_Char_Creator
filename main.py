#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import isBool
from utils.util import Roll_Level

print(style.BOLD + f'Welcome to the D&D Random Character Generator ({version})' + style.END)

isTrue = True

while isTrue:
	print('===============================================================')
	userInput = input('Create a new character? (y/n): ').lower()
	isTrue = isBool(userInput)

	if isTrue:
		print('===============================================================')
		CreateNewCharacter()
		user_input = input("Do you want levels to be weighted higher (if n then they are weighted lower)? (y/n) ")
		level = Roll_Level(user_input)
		print('Character level', level)
		bonus_feats = (5 + level//5 + level//2)
		print('Number of bonus feats', bonus_feats)
		#need to devise a way to randomly pick good feats

	else: print('Exiting Character Generator...')


