import serialem as sem

def checkFilling():
	filling = sem.AreDewarsFilling()
	while filling == 1:
		sem.Echo("Dewars are filling...")
		sem.Delay(60)
		filling = sem.AreDewarsFilling()