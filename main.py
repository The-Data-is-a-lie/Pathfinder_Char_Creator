#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.data import version
from utils.util import isBool
from utils.markdown import style

print(style.BOLD + f"Welcome to the DnD Random Character Generator ({version})" + style.END)

isTrue = True

while isTrue != False:
	print("===============================================================")
	userInput = input("Create a new character?: ")
	userInput = userInput.lower()
	isTrue = isBool(userInput)

	if isTrue == True:
		print("===============================================================")
		CreateNewCharacter()
	else:
		print("Exiting Character Generator...")
