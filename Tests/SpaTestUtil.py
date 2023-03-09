############################################################################
# Test functions
############################################################################
import sys  
import os
import glob
import traceback


# Open source spatial libraries
import shapely
import numpy
sys.path.append(r'../../')

# SpaPy libraries
from SpaPy import SpaVectors
from SpaPy import SpaView
from SpaPy import SpaReferencing
from SpaPy import SpaDensify
from SpaPy import SpaRasters

############################################################################
# Setup functions
############################################################################
def SetupOutputFolder(OutputFolderPath):
	if not os.path.exists(OutputFolderPath): os.makedirs(OutputFolderPath)
	
	TheFiles = glob.glob(OutputFolderPath+"/*.*")
	
	for TheFile in TheFiles:
		try:
				os.remove(TheFile)
		except OSError as e:
			print("Error: %s : %s" % (TheFile, e.strerror))

############################################################################
# HTML functions
############################################################################
# Functions to open and close an HTML file
def HTMLOpen(FilePath):
	global TheHTMLFile
	TheHTMLFile=open(FilePath,"w")
	TheHTMLFile.write("<html>\n")
	TheHTMLFile.write("<body>\n")

def HTMLClose():
	global TheHTMLFile
	TheHTMLFile.write("</body>\n")
	TheHTMLFile.write("</html>\n")
	TheHTMLFile.close()

# Functions to add simple HTML elements to the page
def HTMLHeading(TheHeading,Level=1):
	global TheHTMLFile
	print(TheHeading)
	TheHTMLFile.write("<h"+format(Level)+">"+TheHeading+"</h"+format(Level)+">\n")

def HTMLParagraph(TheText,Level=1):
	global TheHTMLFile
	TheHTMLFile.write("<p>"+TheText+"</p>\n")

def HTMLImage(TheSource):
	global TheHTMLFile
	TheHTMLFile.write("<img src='"+TheSource+"'>\n")


def HTMLError(TheException):
	global TheHTMLFile
	print("Sorry, an error has occurred: "+format(TheException))
	exc_type, exc_value, exc_traceback =sys.exc_info()
	print(exc_type)
	print(exc_value)
	traceback.print_tb(exc_traceback, limit=10)
	#TheText=format(TheText)
	#TheText="<p>Error: %s</p>" % TheText
	TheHTMLFile.write("<p style='color:red'>Error: "+format(TheException)+"</p>\n")

# Functions add tables to the page
def HTMLTableStart():
	global TheHTMLFile
	TheHTMLFile.write("<table>\n")

def HTMLTableHeader(Cells):
	global TheHTMLFile

	TheHTMLFile.write("<tr>\n")

	Index=0
	while (Index<len(Cells)):
		TheHTMLFile.write("<th>"+format(Cells[Index])+"</th>\n")
		Index+=1

	TheHTMLFile.write("</tr>\n")

def HTMLTableRow(Cells):
	global TheHTMLFile

	TheHTMLFile.write("<tr>\n")
	Index=0
	while (Index<len(Cells)):
		TheHTMLFile.write("<td>"+format(Cells[Index])+"</td>\n")
		Index+=1
	TheHTMLFile.write("</tr>\n")

def HTMLTableEnd():
	global TheHTMLFile
	TheHTMLFile.write("</table>\n")

def RenderDatasetToImage(TheDataset,TheFilePath):
	TheBounds=TheDataset.GetBounds()
	MinX=TheBounds[0]
	MinY=TheBounds[1]
	MaxX=TheBounds[2]
	MaxY=TheBounds[3]

	TheView=SpaView.SpaView(500,500)
	TheView.SetBounds(MinX,MaxX,MinY,MaxY)

	TheLayer=None
	if (isinstance(TheDataset,SpaRasters.SpaDatasetRaster)):
		TheView.RenderRaster(TheDataset)
	else:
		TheLayer=SpaVectors.SpaLayerVector()
		TheLayer.SetDataset(TheDataset)
		TheLayer.Render(TheView)
	TheView.Save(TheFilePath)

def HTMLRenderDataset(TheDataset,OutputFolderPath,TheFileName):
	RenderDatasetToImage(TheDataset,OutputFolderPath+TheFileName)
	HTMLImage(TheFileName)