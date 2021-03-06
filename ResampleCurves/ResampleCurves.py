import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import math
import numpy as np

#
# ResampleCurves
#

class ResampleCurves(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ResampleCurves" # TODO make this more human readable by adding spaces
    self.parent.categories = ["SlicerMorph"]
    self.parent.dependencies = []
    self.parent.contributors = ["Sara Rolfe (UW), Murat Maga (UW)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This module imports curve markups saved as FCSV files from a directory, resamples them at the requested sample rate and saves them to the output directory selected.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This module was developed by Sara Rolfe and Murat Maga, through a NSF ABI Development grant, "An Integrated Platform for Retrieval, Visualization and Analysis of
3D Morphology From Digital Biological Collections" (Award Numbers: 1759883 (Murat Maga), 1759637 (Adam Summers), 1759839 (Douglas Boyer)).
https://nsf.gov/awardsearch/showAward?AWD_ID=1759883&HistoricalAwards=false
""" # replace with organization, grant and thanks.

#
# ResampleCurvesWidget
#

class ResampleCurvesWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # Select landmark file to import
    #
    self.inputDirectory = ctk.ctkPathLineEdit()
    self.inputDirectory.filters = ctk.ctkPathLineEdit.Dirs
    self.inputDirectory.setToolTip( "Select directory containing curves to resample" )
    parametersFormLayout.addRow("Input Directory:", self.inputDirectory)


    #
    # output directory selector
    #
    self.outputDirectory = ctk.ctkPathLineEdit()
    self.outputDirectory.filters = ctk.ctkPathLineEdit.Dirs
    self.outputDirectory.currentPath = slicer.app.temporaryPath
    parametersFormLayout.addRow("Output Directory:", self.outputDirectory)

    #
    # Get Resample number
    #
    self.ResampleRateWidget = ctk.ctkDoubleSpinBox()
    self.ResampleRateWidget.value = 50
    self.ResampleRateWidget.minimum = 3
    self.ResampleRateWidget.maximum = 5000
    self.ResampleRateWidget.singleStep = 1
    self.ResampleRateWidget.setDecimals(0)
    self.ResampleRateWidget.setToolTip("Select the number of points for resampling: ")
    parametersFormLayout.addRow("Output sample number: ", self.ResampleRateWidget)

    #
    # Get open or closed curve option
    #
    curveTypeSelector = qt.QHBoxLayout()
    self.curveTypeOpen=qt.QRadioButton("open")
    self.curveTypeOpen.setToolTip("Select option for no interpolation between first and last points")
    self.curveTypeOpen.setChecked(True)
    self.curveTypeClosed=qt.QRadioButton("closed")
    self.curveTypeClosed.setToolTip("Select option to interpolate between first and last points")
    curveTypeSelector.addWidget(self.curveTypeOpen)
    curveTypeSelector.addWidget(self.curveTypeClosed)
    curveTypeSelector.addStretch()
    parametersFormLayout.addRow("Curve Type: ",curveTypeSelector)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)


    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the conversion."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputDirectory.connect('validInputChanged(bool)', self.onSelectInput)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelectInput()
    #self.onSelectOutput()

  def cleanup(self):
    pass

  def onSelectInput(self):
    self.applyButton.enabled = bool(self.inputDirectory.currentPath)


  def onApplyButton(self):
    logic = ResampleCurvesLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    logic.run(self.inputDirectory.currentPath, self.outputDirectory.currentPath, int(self.ResampleRateWidget.value), self.curveTypeClosed.isChecked())

#
# ResampleCurvesLogic
#

class ResampleCurvesLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qimage = ctk.ctkWidgetsUtils.grabWidget(widget)
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def ResamplePoints(self, originalPoints, sampledPoints, samplingDistance, closedCurve):
    if (not originalPoints or not sampledPoints or samplingDistance <= 0):
      print("ResamplePoints failed: invalid inputs")
      return False
    if (originalPoints.GetNumberOfPoints() < 2):
      sampledPoints.DeepCopy(originalPoints)
      return True

    distanceFromLastSampledPoint = 0
    previousCurvePoint = originalPoints.GetPoint(0)
    sampledPoints.Reset()
    sampledPoints.InsertNextPoint(previousCurvePoint) # First point in new set is always point 0
    numberOfOriginalPoints = originalPoints.GetNumberOfPoints()
    totalSegmentLength = 0;
    for originalPointIndex in range(numberOfOriginalPoints):
      currentCurvePoint = originalPoints.GetPoint(originalPointIndex)
      segmentLength = math.sqrt(vtk.vtkMath().Distance2BetweenPoints(currentCurvePoint,previousCurvePoint))
      totalSegmentLength+=segmentLength
      if segmentLength <= 0:
        continue

      remainingSegmentLength = distanceFromLastSampledPoint + segmentLength
      if round(remainingSegmentLength,4) >= round(samplingDistance,4):
        segmentDirectionVector = np.array([
          (currentCurvePoint[0] - previousCurvePoint[0]) / segmentLength,
          (currentCurvePoint[1] - previousCurvePoint[1]) / segmentLength,
          (currentCurvePoint[2] - previousCurvePoint[2]) / segmentLength
          ])
        # distance of new sampled point from previous curve point
        distanceFromLastInterpolatedPoint = samplingDistance - distanceFromLastSampledPoint
        while (round(remainingSegmentLength,4) >= round(samplingDistance,4)):
          newSampledPoint = np.array([
            previousCurvePoint[0] + segmentDirectionVector[0] * distanceFromLastInterpolatedPoint,
            previousCurvePoint[1] + segmentDirectionVector[1] * distanceFromLastInterpolatedPoint,
            previousCurvePoint[2] + segmentDirectionVector[2] * distanceFromLastInterpolatedPoint
            ])
          sampledPoints.InsertNextPoint(newSampledPoint)
          distanceFromLastSampledPoint = 0
          distanceFromLastInterpolatedPoint += samplingDistance
          remainingSegmentLength -= samplingDistance
        distanceFromLastSampledPoint = remainingSegmentLength
      else:
        distanceFromLastSampledPoint += segmentLength
      previousCurvePoint = currentCurvePoint

    return True

  def run(self, inputDirectory, outputDirectory, resampleNumber, closedCurveOption):
    extension = ".fcsv"
    for file in os.listdir(inputDirectory):
      if file.endswith(extension):
        # read landmark file
        inputFilePath = os.path.join(inputDirectory, file)
        markupsNode =slicer.util.loadMarkupsFiducialList(inputFilePath)

        #resample
        if closedCurveOption:
          curve = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsClosedCurveNode", "resampled_temp")
          resampledCurve = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsClosedCurveNode", "resampledClosedCurve")

        else:
          curve = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", "resampled_temp")
          resampledCurve = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", "resampledCurve")


        vector=vtk.vtkVector3d()
        pt=[0,0,0]
        landmarkNumber = markupsNode.GetNumberOfFiducials()

        for landmark in range(0,landmarkNumber):
          markupsNode.GetMarkupPoint(landmark,0,pt)
          vector[0]=pt[0]
          vector[1]=pt[1]
          vector[2]=pt[2]
          curve.AddControlPoint(vector)

        currentPoints = curve.GetCurvePointsWorld()
        newPoints = vtk.vtkPoints()

        if closedCurveOption:
          sampleDist = curve.GetCurveLengthWorld()/(resampleNumber)
        else:
          sampleDist = curve.GetCurveLengthWorld()/(resampleNumber-1)

        curve.ResamplePoints(currentPoints, newPoints,sampleDist,closedCurveOption)

        #set resampleNumber control points
        if (newPoints.GetNumberOfPoints() == resampleNumber) or (closedCurveOption and (newPoints.GetNumberOfPoints() == resampleNumber+1)) :
          for controlPoint in range(0,resampleNumber):
            newPoints.GetPoint(controlPoint,pt)
            vector[0]=pt[0]
            vector[1]=pt[1]
            vector[2]=pt[2]
            resampledCurve.AddControlPoint(vector)

          newPointNumber = resampledCurve.GetNumberOfControlPoints()

          # save
          newFileName = os.path.splitext(file)[0] + "_resample_" +str(newPointNumber) + extension
          outputFilePath = os.path.join(outputDirectory, newFileName)
          slicer.util.saveNode(resampledCurve, outputFilePath)
          slicer.mrmlScene.RemoveNode(markupsNode)  #remove node from scene
          slicer.mrmlScene.RemoveNode(curve)
          slicer.mrmlScene.RemoveNode(resampledCurve)
        else:
          print("Error: resampling did not return expected number of points")
          print("Resampled Points: ", newPoints.GetNumberOfPoints())

    logging.info('Processing completed')

    return True

  def hasImageData(self, volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True


class ResampleCurvesTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_ResampleCurves1()

  def test_ResampleCurves1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """
    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
    SampleData.downloadFromURL(
      nodeNames='FA',
      fileNames='FA.nrrd',
      uris='http://slicer.kitware.com/midas3/download?items=5767',
      checksums='SHA256:12d17fba4f2e1f1a843f0757366f28c3f3e1a8bb38836f0de2a32bb1cd476560')
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = ResampleCurvesLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
