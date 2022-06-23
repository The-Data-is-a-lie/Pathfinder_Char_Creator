#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.data import version
from utils.util import isBool
from utils.markdown import style

print(style.BOLD + f'Welcome to the D&D Random Character Generator ({version})' + style.END)

isTrue = True

while isTrue:
	print('===============================================================')
	userInput = input('Create a new character? (y/n): ').lower()
	isTrue = isBool(userInput)

	if isTrue:
		print('===============================================================')
		CreateNewCharacter()

	else:
		print('Exiting Character Generator...')
