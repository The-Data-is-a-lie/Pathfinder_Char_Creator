#Internal Imports
from utils.util import RollStat

#External imports
import random

gold = RollStat()
silver = RollStat()
copper = RollStat()

def currentRate():
	"""
	used for random exchange rates between different made up currencies
	- Returns
	- Exchange Rates (String)
	"""
	currRate = 1 + (100-1)*random.random()
	currRate1 = 1 + (100-1)*random.random()
	currRate2 = 1 + (100-1)*random.random()
	
	print(f"All Currencies:\npp: Platinum Piece\nc: Credits\nes: Elven Syenos\n")
	print(f"Exchange Rate:")
	print(f"1gp => 100sp")
	print(f"1sp => 100cp")
	print(f"1gp => {round(currRate, 2)}pp")
	print(f"1gp => {round(currRate1, 2)}c")
	print(f"1gp => {round(currRate2, 2)}es\n")

def TotalCoinsHeld():
	print(f"Gold (gp): {gold}gp\nSilver (sp): {silver}sp\nCopper (cp): {copper}cp\n")

def runCurrency():
	TotalCoinsHeld()
	currentRate()