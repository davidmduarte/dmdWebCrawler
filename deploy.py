# deploy
# Autor: David Duarte
# Build 6 - primeira versao funcional
# Build 5 - delpoy esta a funcionar o zip ainda nao

binDir = "./"
deployDir = "./WebCrawler"

import os
import sys
import shutil
import zipfile

# Get Build number
f = open(".deployCnt", "r")
buildNum = f.read()
f.close()

if len(sys.argv) > 1: # make zip
	if sys.argv[1].upper() == "ZIP":
		# open the zip file for writing, and write stuff to it
		file = zipfile.ZipFile(deployDir[2:] + "_build_" + buildNum + ".zip", "a")
		for item in os.listdir(deployDir):
			newPath = os.path.join(deployDir, item) 
			file.write(newPath, os.path.basename(newPath), zipfile.ZIP_DEFLATED)
		file.close()
else: #deploy
	print("Deploying ...")
	
	if not os.path.isdir(deployDir):
		os.mkdir(deployDir)
	
	#List all pyc e move to the deployDir
	for item in os.listdir(binDir):
		newFilename = item.split('.')
		if newFilename[-1] == "pyc":
			newFilename = newFilename[0] + '.' + newFilename[-1]
			shutil.move(
				os.path.join(binDir, item),
				os.path.join(deployDir, newFilename))
	shutil.copy(
		os.path.join(binDir, "startCrawler.py"),
		os.path.join(deployDir, "startCrawler.py"))
				
	# Set Build number
	f = open(".deployCnt", "w")
	f.write(str(int(buildNum)+1))
	f.close()
	print("Build Num: " + str(int(buildNum)+1))
	
	print("done.")