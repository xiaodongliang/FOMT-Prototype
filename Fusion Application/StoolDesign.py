#Author-Brian Ekins
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback
import math, random
import os
import tempfile
import uuid
import adsk.core, adsk.fusion, traceback
from .Packages import requests
from .Packages import sendpart
import base64


_app = adsk.core.Application.get()
_ui  = _app.userInterface
_handlers = []



# All values are in centimeters.
_seatWidth = 21
_seatHeight = 41
_minSize = 1 * 2.54 
_strokeTol = 0.005 
_retractHeight = 0.5
_cuttingDepths = [-0.09, -0.1]


payload_data = dict()
init_values = dict()  # store text boxes entries
# Initialize to empty
init_values['company_name'] = ""
init_values['name'] = ""
init_values['email'] = ""
init_values['phone'] = ""
init_values['part_number'] = ""
init_values['part_count'] = "100-999"
init_values['material_type'] = ""
init_values['material_grade'] = ""
init_values['cnc_upload'] = False

 
class CutSeatCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
             
            app = adsk.core.Application.get()
            ui = app.userInterface
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs
           

            
            # Create uuid
            transaction_id = str(uuid.uuid1())
            
            init_values['part_number'] = inputs.itemById('part_number_val').value
            init_values['part_count'] = inputs.itemById('part_count_val').selectedItem.name
            init_values['material_type'] = inputs.itemById('material_type_val').value
            
            # Pack the Payload
            payload_data['part_number'] = inputs.itemById('part_number_val').value
            payload_data['material_type'] = inputs.itemById('material_type_val').value
            payload_data['part_count'] = inputs.itemById('part_count_val').selectedItem.name
            
            payload_data['cnc_upload'] = inputs.itemById('cnc_upload').value


            # Instantiate Export Manager
            current_design_context = app.activeProduct
            export_manager = current_design_context.exportManager
            
             # Select Part
            try:
                selected_part = inputs.itemById('upload_file').selection(0).entity
                if selected_part.objectType == adsk.fusion.Occurrence.classType():
                    selected_part = selected_part.component
            except:
                ui.messageBox('Unable to Process Selection:\n{}'.format(traceback.format_exc()))
                return
                
            # Export part into temp dir
            try:
                 #snapshot of the model
                ui.activeSelections.clear()
                output_snapshot_name = tempfile.mkdtemp()+'//'+ transaction_id +'.jpg'
                app.activeViewport.saveAsImageFile(output_snapshot_name, 300, 300)  
                encoded_string = ''
                with open(output_snapshot_name, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())                
                payload_data['snapshot'] = encoded_string 
                
                
                if payload_data['cnc_upload']:
                    #export to fusion 360 archive with texture 
                    #and also upload CNC data
                
                    payload_data['uuid'] = transaction_id + '.f3d'
                    output_file_name = tempfile.mkdtemp()+'//'+ transaction_id +'.f3d'
                    options = export_manager.createFusionArchiveExportOptions(output_file_name, selected_part)
                    export_manager.execute(options)
                    temp = {'file': open(output_file_name, 'rb')}
                  


                    # Send to admin platform
                    response = sendpart.send('https://au-china-forge.herokuapp.com/ForgeRoute/uploadfusionfile', payload_data, temp, 30)
                    #ui.messageBox('model file uploading' + response) 
                    
                    gCode = generateGCode_JSON() 
                    output_file_name = tempfile.mkdtemp()+'//'+ transaction_id +'.json'
                    text_file = open(output_file_name, "w")
                    text_file.write(gCode)
                    text_file.close()
                    
                    temp = {'file': open(output_file_name, 'rb')}
                    response = sendpart.send('https://au-china-forge.herokuapp.com/ForgeRoute/uploadcncfile', payload_data, temp, 30)
                    ui.messageBox('cnc data uploading:'+ response)  
                    
                    
                else:                    
                    #export to step file. no texture
                    payload_data['uuid'] = transaction_id + '.step'
                    output_file_name = tempfile.mkdtemp()+'//'+ transaction_id +'.step'
                    options = export_manager.createSTEPExportOptions(output_file_name, selected_part)
                    export_manager.execute(options)
                    temp = {'file': open(output_file_name, 'rb')}

                    # Send to admin platform
                    response = sendpart.send('https://au-china-forge.herokuapp.com/ForgeRoute/uploadfusionfile', payload_data, temp, 30)
                    ui.messageBox(response) 
               
            except:
                ui.messageBox('Unable to Export Selection:\n{}'.format(traceback.format_exc()))
                return
            
            
            
            
#            gCode = generateGCode()
#            gCode = generateGCode_JSON()
#
#            description = inputs.itemById('descriptionInput').value
#            isDebug = inputs.itemById('debugInput').value
#            
#            text_file = open("C:/Temp/g-codeTest.txt", "w")
#            text_file.write(gCode)
#            text_file.close()
#            
#            if gCode == '':
#                return False
#                
#            # Get list of tools on the network
#            from .Modules import fabmo    
#            try:
#                tools = fabmo.find_tools(debug=isDebug)
#            except:
#                _ui.messageBox('Unable to use the Fabmo tools.  Aborting.')
#                return False
#        
#            # Make sure we have one and only one tool
#            if len(tools) == 0:
#                _ui.messageBox('No tools were found on the network.')
#                return
#            elif len(tools) > 1:
#                _ui.messageBox('There is more than one tool on the network.')
#                return
#        
#            tool = tools[0]
#            
#            job = tool.submit_job(gCode, 'stool.nc', 'Fusion 360 design. ' + description)
#            
#            _ui.messageBox('Job submitted.')
#            tool.show_job_manager()
            
            #return True
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
                
                
# Event handler for the Cut Seat command created event.
class CutSeatCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
    
            
            # Connect to the execute event.
            onExecute = CutSeatCommandExecuteHandler()
            eventArgs.command.execute.add(onExecute)
            _handlers.append(onExecute)
            
            onValidateInputs = CutSeatValidateInputsHandler()
            eventArgs.command.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)
    
            inputs = eventArgs.command.commandInputs
            cmd = eventArgs.command
            
            cmd.commandCategoryName = 'MakeTime Request'
            cmd.setDialogInitialSize(400, 400)
            cmd.setDialogMinimumSize(400, 400)

            
             # Logo here
            inputs.addTextBoxCommandInput('spacer_1', '', '', 1, True)
            inputs.addImageCommandInput('logo_image', '', './/Resources//adsk.png')
            inputs.addTextBoxCommandInput('spacer_2', '', '', 2, True)
            
            inputs.addTextBoxCommandInput('spacer_3', '','<hr>', 1, True)
            inputs.addTextBoxCommandInput('Part Description', '', '<h3 style="color:#000000;">零件描述</h3>', 2, True)
            
             # Select the file to upload
            file_select = inputs.addSelectionInput('upload_file', 'Select for Upload', '')
            file_select.addSelectionFilter('Occurrences')
            file_select.addSelectionFilter('RootComponents')

            # Get user input about part
            #inputs.addStringValueInput('part_number_val', '零件代号', init_values['part_number'])
            inputs.addStringValueInput('part_number_val', 'Part Number', init_values['part_number'])

            #dropdown = inputs.addDropDownCommandInput('part_count_val', '制造个数', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            dropdown = inputs.addDropDownCommandInput('part_count_val', 'Quantity', adsk.core.DropDownStyles.LabeledIconDropDownStyle)  
            dropdownItems = dropdown.listItems
            if 'part_count' in init_values:
                select_dropdown = init_values['part_count']
            else:
                select_dropdown = '100-999'
            if select_dropdown == '1-9':
                dropdownItems.add('1-9', True, '')
            else:
                dropdownItems.add('1-9', False, '')
            if select_dropdown == '10-99':
                dropdownItems.add('10-99', True, '')
            else:
                dropdownItems.add('10-99', False, '')
            if select_dropdown == '100-999':
                dropdownItems.add('100-999', True, '')
            else:
                dropdownItems.add('100-999', False, '')
            if select_dropdown == '1000+':
                dropdownItems.add('1000+', True, '')
            else:
                dropdownItems.add('1000+', False, '')

#            inputs.addStringValueInput('material_type_val', '材料', init_values['material_type'])
#            inputs.addBoolValueInput('cnc_upload', '含材质和机加工数据',True, '',init_values['cnc_upload'])
            inputs.addStringValueInput('material_type_val', 'Material', init_values['material_type'])
            inputs.addBoolValueInput('cnc_upload', 'Include CNC',True, '',init_values['cnc_upload'])
 

 

            # Make it button
            #cmd.okButtonText = '提交任务'
            cmd.okButtonText = 'Submit'
            
            
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            


class CutSeatValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
        inputs = eventArgs.inputs
        
#        eventArgs.areInputsValid = True
#        if inputs.itemById('nameInput').value == '':
#            eventArgs.areInputsValid = False
#
#        if inputs.itemById('emailInput').value == '':
#            eventArgs.areInputsValid = False


def generateGCode():
    try:
        des = adsk.fusion.Design.cast(_app.activeProduct)

        ### Get all of the sketch geometry as polylines for sketches that are
        ### based on the x-y construction plane, are visuble and have "cut" in the name.      
        polyLines = []
        sk = adsk.fusion.Sketch.cast(None)
        for sk in des.rootComponent.sketches:
            # Get the visible design sketches.
            if sk.isVisible:
                # Check the sketch name contains "cut"
                if sk.name.upper().find('CUT') != -1:
                    # Iterate over all of the curves in the sketch.
                    curve = adsk.fusion.SketchCurve.cast(None)
                    for curve in sk.sketchCurves:
                        if not curve.isConstruction:
                            # Get a line approximation of the curve.
                            eval = adsk.core.CurveEvaluator3D.cast(curve.geometry.evaluator)
                            (returnValue, startParameter, endParameter) = eval.getParameterExtents()
                            (returnValue, vertexCoordinates) = eval.getStrokes(startParameter, endParameter, _strokeTol)
                            curvePoly = polyLine(vertexCoordinates)
    
                            if len(polyLines) == 0:
                                polyLines.append(curvePoly)
                            else:
                                # Iterate over all existing polylines to see if this connects.
                                didConnect = False
                                for poly in polyLines:
                                    didConnect = poly.connect(curvePoly)
                                    if didConnect:
                                        break
                                if not didConnect:
                                    polyLines.append(curvePoly)

                    ###### Iterate through all text.
                    text = adsk.fusion.SketchText.cast(None)
                    for text in sk.sketchTexts:
                        textCurves = text.asCurves()
                        for textCurve in textCurves:
                            # Get a line approximation of the curve.
                            eval = adsk.core.CurveEvaluator3D.cast(textCurve.evaluator)
                            (returnValue, startParameter, endParameter) = eval.getParameterExtents()
                            (returnValue, vertexCoordinates) = eval.getStrokes(startParameter, endParameter, _strokeTol)
                            curvePoly = polyLine(vertexCoordinates)

                            if len(polyLines) == 0:
                                polyLines.append(curvePoly)
                            else:
                                # Iterate over all existing polylines to see if this connects.
                                didConnect = False
                                for poly in polyLines:
                                    didConnect = poly.connect(curvePoly)
                                    if didConnect:
                                        break
                                if not didConnect:
                                    polyLines.append(curvePoly)

        # Continue to try to reconnect the curves until nothing can be connected.
        connected = True
        while connected:
            connected = False
            for poly1 in polyLines:
                index = -1
                for poly2 in polyLines:
                    index += 1
                    if poly1 and poly2:
                        if not poly1 is poly2:
                            didConnect = poly1.connect(poly2)
                            if didConnect:
                                polyLines[index] = None
                                connected = True
                                
        # Clean up the polyline list.
        for i in range(len(polyLines)-1, -1, -1):
            if not polyLines[i]:
                polyLines.pop(i)
                
        # Reorder and reverse the polylines to create the optimal cutting path.
        for i in range(0, len(polyLines)-1):
            closestPoly = -1
            closestDist = 500000
            isStart = True
            lastPoint = polyLines[i].endPoint()
            for j in range(i+1, len(polyLines)):
                dist = polyLines[j].startPoint().distanceTo(lastPoint)
                if dist < closestDist:
                    closestDist = dist
                    closestPoly = j
                    isStart = True
                    
                dist = polyLines[j].endPoint().distanceTo(lastPoint)
                if dist < closestDist:
                    closestDist = dist
                    closestPoly = j
                    isStart = False
                    
            if not isStart:
                polyLines[closestPoly].reverse()
                
            if polyLines[closestPoly] != polyLines[i+1]:
                tempPoly = polyLines[i+1]
                polyLines[i+1] = polyLines[closestPoly]
                polyLines[closestPoly] = tempPoly
                
        ###### Begin creating the g-code data.        
        # Write the header.
        
        gCode = ''
        gCode += 'g20\n'        # set to inches
        gCode += 'g1 f120\n'     # set the feed rate.
        gCode += 'g0 z' + toInches(_retractHeight) + '\n'    # lift to safe Z
        gCode += 'm4\n'         # spindle on
        gCode += 'g4 p2\n'      # a pause to allow spindle to spin up   

        # Do a pass for each cutting depth.        
        for cuttingDepth in _cuttingDepths:
            for poly in polyLines:
                firstPoint = True
                for point in poly.points:
                    if firstPoint:
                        # Move to start of polyline and then drop down.
                        gCode += ('g0 x' + toInches(point.x) + ' y' + 
                                 toInches(point.y) + '\n')
                        gCode += 'g1 z' + toInches(cuttingDepth) + '\n'
                        gCode += ('g1 x' + toInches(point.x) + ' y' + 
                                 toInches(point.y) + '\n')
                        firstPoint = False
                    else:
                        gCode += ('g1 x' + toInches(point.x) + ' y' + 
                                 toInches(point.y) + '\n')
                
                # Retract to safe Z
                gCode += 'g0 z' + toInches(_retractHeight) + '\n'
                    
        # Write the end of the data.
        gCode += 'm5\n'         # turn off spindle
        gCode += 'g0 x24 y0\n'   # Go to home.
        gCode += 'm30\n'        # End of Program
        
        return gCode
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        return ''

def generateGCode_JSON():
    try:
        des = adsk.fusion.Design.cast(_app.activeProduct)

        ### Get all of the sketch geometry as polylines for sketches that are
        ### based on the x-y construction plane, are visuble and have "cut" in the name.      
        polyLines = []
        sk = adsk.fusion.Sketch.cast(None)
        for sk in des.rootComponent.sketches:
            # Get the visible design sketches.
            if sk.isVisible:
                # Check the sketch name contains "cut"
                if sk.name.upper().find('CUT') != -1:
                    # Iterate over all of the curves in the sketch.
                    curve = adsk.fusion.SketchCurve.cast(None)
                    for curve in sk.sketchCurves:
                        if not curve.isConstruction:
                            # Get a line approximation of the curve.
                            eval = adsk.core.CurveEvaluator3D.cast(curve.geometry.evaluator)
                            (returnValue, startParameter, endParameter) = eval.getParameterExtents()
                            (returnValue, vertexCoordinates) = eval.getStrokes(startParameter, endParameter, _strokeTol)
                            curvePoly = polyLine(vertexCoordinates)
    
                            if len(polyLines) == 0:
                                polyLines.append(curvePoly)
                            else:
                                # Iterate over all existing polylines to see if this connects.
                                didConnect = False
                                for poly in polyLines:
                                    didConnect = poly.connect(curvePoly)
                                    if didConnect:
                                        break
                                if not didConnect:
                                    polyLines.append(curvePoly)

                    ###### Iterate through all text.
                    text = adsk.fusion.SketchText.cast(None)
                    for text in sk.sketchTexts:
                        textCurves = text.asCurves()
                        for textCurve in textCurves:
                            # Get a line approximation of the curve.
                            eval = adsk.core.CurveEvaluator3D.cast(textCurve.evaluator)
                            (returnValue, startParameter, endParameter) = eval.getParameterExtents()
                            (returnValue, vertexCoordinates) = eval.getStrokes(startParameter, endParameter, _strokeTol)
                            curvePoly = polyLine(vertexCoordinates)

                            if len(polyLines) == 0:
                                polyLines.append(curvePoly)
                            else:
                                # Iterate over all existing polylines to see if this connects.
                                didConnect = False
                                for poly in polyLines:
                                    didConnect = poly.connect(curvePoly)
                                    if didConnect:
                                        break
                                if not didConnect:
                                    polyLines.append(curvePoly)

        # Continue to try to reconnect the curves until nothing can be connected.
        connected = True
        while connected:
            connected = False
            for poly1 in polyLines:
                index = -1
                for poly2 in polyLines:
                    index += 1
                    if poly1 and poly2:
                        if not poly1 is poly2:
                            didConnect = poly1.connect(poly2)
                            if didConnect:
                                polyLines[index] = None
                                connected = True
                                
        # Clean up the polyline list.
        for i in range(len(polyLines)-1, -1, -1):
            if not polyLines[i]:
                polyLines.pop(i)
                
        # Reorder and reverse the polylines to create the optimal cutting path.
        for i in range(0, len(polyLines)-1):
            closestPoly = -1
            closestDist = 500000
            isStart = True
            lastPoint = polyLines[i].endPoint()
            for j in range(i+1, len(polyLines)):
                dist = polyLines[j].startPoint().distanceTo(lastPoint)
                if dist < closestDist:
                    closestDist = dist
                    closestPoly = j
                    isStart = True
                    
                dist = polyLines[j].endPoint().distanceTo(lastPoint)
                if dist < closestDist:
                    closestDist = dist
                    closestPoly = j
                    isStart = False
                    
            if not isStart:
                polyLines[closestPoly].reverse()
                
            if polyLines[closestPoly] != polyLines[i+1]:
                tempPoly = polyLines[i+1]
                polyLines[i+1] = polyLines[closestPoly]
                polyLines[closestPoly] = tempPoly
                
        ###### Begin creating the g-code data.        
        # Write the header.
        
        gCode = '{"gcode":'
        gCode += '[{"type":"g20","value":""},'        # set to inches
        gCode += '{"type":"g1","value": "f120"},'     # set the feed rate.
        gCode += '{"type":"g0","value":{"z":' + toInches(_retractHeight) + '}},'    # lift to safe Z
        gCode += '{"type":"m4","value":""},'         # spindle on
        gCode += '{"type":"g4","value":"p2"},'      # a pause to allow spindle to spin up   

        # Do a pass for each cutting depth.        
        for cuttingDepth in _cuttingDepths:
            for poly in polyLines:
                firstPoint = True
                for point in poly.points:
                    if firstPoint:
                        # Move to start of polyline and then drop down.
                        gCode += ('{"type":"g0","value":{"x":' + toInches(point.x) + ',"y":' + 
                                 toInches(point.y) + '}},')
                        gCode += '{"type":"g1","value":{"z":' + toInches(cuttingDepth) + '}},'
                        gCode += ('{"type":"g1","value":{"x":' + toInches(point.x) + ',"y":' + 
                                 toInches(point.y) + '}},')
                        firstPoint = False
                    else:
                        gCode += ('{"type":"g1","value":{"x":' + toInches(point.x) + ',"y":' + 
                                 toInches(point.y) + '}},')
                
                # Retract to safe Z
                gCode += '{"type":"g0","value":{"z":' + toInches(_retractHeight) + '}},'
                    
        # Write the end of the data.
        gCode += '{"type":"m5","value":""},'         # turn off spindle
        gCode += '{"type":"g0","value":{"x":24, "y":0}},'   # Go to home.
        gCode += '{"type":"m30","value":""}'        # End of Program
        gCode += ']}';
        return gCode
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        return ''

def generateGCodeOld():
    try:
        des = adsk.fusion.Design.cast(_app.activeProduct)
    
        # Begin creating the g-code data.
        gCode = ''
        
        # Write the header.
        gCode += 'g20\n'        # set to inches
        gCode += 'g1 f120\n'     # set the feed rate.
        gCode += 'g0 z' + toInches(_retractHeight) + '\n'    # lift to safe Z
        gCode += 'm4\n'         # spindle on
        gCode += 'g4 p2\n'      # a pause to allow spindle to spin up   
    
        # Get the visible design sketches.
        sk = adsk.fusion.Sketch.cast(None)
        for sk in des.rootComponent.sketches:
            if sk.isVisible:
                attrib = sk.attributes.itemByName('adsk-Seat', 'SeatSketch')
                if attrib:   
                    #**** Iterate through the lines in the sketch.
                    for cuttingDepth in _cuttingDepths:
                        lastPnt = adsk.core.Point3D.create(-1000,-1000,-1000)
                        skLine = adsk.fusion.SketchLine.cast(None)
                        for skLine in sk.sketchCurves.sketchLines:
                            if not skLine.isConstruction:
                                startPnt = skLine.startSketchPoint.geometry
                                endPnt = skLine.endSketchPoint.geometry
                                if startPnt.isEqualTo(lastPnt):
                                    gCode += ('g1 x' + toInches(endPnt.x) + ' y' + 
                                             toInches(endPnt.y) + '\n')
                                    lastPnt = endPnt
                                else:
                                    gCode += 'g0 z' + toInches(_retractHeight) + '\n'
                                    gCode += ('g0 x' + toInches(startPnt.x) + ' y' + 
                                             toInches(startPnt.y) + '\n')
                                    gCode += 'g1 z' + toInches(cuttingDepth) + '\n'
                                    gCode += ('g1 x' + toInches(endPnt.x) + ' y' + 
                                             toInches(endPnt.y) + '\n')
                                    lastPnt = endPnt
                        
                        # Retract to safe Z
                        gCode += 'g0 z' + toInches(_retractHeight) + '\n'    
                                                
                    #**** Iterate through all other curve types.
                    curve = adsk.fusion.SketchCurve.cast(None)
                    for curve in sk.sketchCurves:
                        if curve.objectType != adsk.fusion.SketchLine.classType():
                            # Get a line approximation of the circle.
                            eval = adsk.core.CurveEvaluator3D.cast(curve.geometry.evaluator)
                            (returnValue, startParameter, endParameter) = eval.getParameterExtents()
                            (returnValue, vertexCoordinates) = eval.getStrokes(startParameter, endParameter, _strokeTol)
                            
                            # Create the cutting path at each cut depth.
                            for cuttingDepth in _cuttingDepths:
                                firstPnt = True
                                for coord in vertexCoordinates:
                                    # Write the point to the file.
                                    if firstPnt:
                                        gCode += 'g0 x' + toInches(coord.x) + ' y' + toInches(coord.y) + '\n'
                                        gCode += 'g1 z' + toInches(cuttingDepth) + '\n'
                                        firstPnt = False
                                    else:
                                        gCode += 'g1 x' + toInches(coord.x) + ' y' + toInches(coord.y) + '\n'
                                        
                                gCode += 'g0 z' + toInches(_retractHeight) + '\n'    # lift to safe Zs
    
        # Write the end of the data.
        gCode += 'm5\n'         # turn off spindle
        gCode += 'g0 x24 y0\n'   # Go to home.
        gCode += 'm30\n'        # End of Program
        
        return gCode
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        return ''


class polyLine():
    def __init__(self, points = None):
        self.isClosed = False
        if points:
            self.points = list(points)
            if self.startPoint().isEqualTo(self.endPoint()):
                self.isClosed = True
        else:
            self.points = []

    def startPoint(self):
        if self.pointCount() == 0:
            return None
        else:
            return self.points[0]
        
    def endPoint(self):
        if self.pointCount() == 0:
            return None
        else:
            return self.points[self.pointCount()-1]
            
    def pointCount(self):
        return len(self.points)
            
    def points(self):
        return self.points
        
    def asString(self):
        result = ''
        for point in self.points:
            result += str(point.x) + ', ' + str(point.y) + ', ' + str(point.z) + '\n'
        return result
        
    def reverse(self):
        self.points.reverse()

    def connects(self, poly):
        if not self.isClosed:
            thisStart = adsk.core.Point3D.cast(self.startPoint())
            thisEnd = adsk.core.Point3D.cast(self.endPoint())
            
            otherStart = poly.startPoint()
            otherEnd = poly.endPoint()
            
            if thisStart.isEqualTo(otherStart):
                return True
            elif thisStart.isEqualTo(otherEnd):
                return True
            elif thisEnd.isEqualTo(otherStart):
                return True
            elif thisEnd.isEqualTo(otherEnd):
                return True
        return False                
       
    def connect(self, poly):
        isConnected = False            
        if not self.isClosed:
            thisStart = adsk.core.Point3D.cast(self.startPoint())
            thisEnd = adsk.core.Point3D.cast(self.endPoint())
            
            otherStart = poly.startPoint()
            otherEnd = poly.endPoint()

            if thisStart.isEqualTo(otherStart):
                # Reverse the other polyline and add it to the front of the existing polyline.
                tempList = list(poly.points)
                tempList.pop(0)
                tempList.reverse()
                self.points = tempList + self.points
                isConnected = True
            elif thisStart.isEqualTo(otherEnd):
                # Add the other polyline to the front of this one maintaining
                # the same point order of the other polyline.
                tempList = list(poly.points)
                tempList.pop(len(tempList)-1)
                self.points = tempList + self.points
                isConnected = True
            elif thisEnd.isEqualTo(otherStart):
                tempList = list(poly.points)
                tempList.pop(0)
                self.points.extend(tempList)
                isConnected = True
            elif thisEnd.isEqualTo(otherEnd):
                tempList = list(poly.points)
                tempList.pop(len(tempList)-1)
                tempList.reverse()
                self.points.extend(tempList)
                isConnected = True

        # Check to see if the polyline is closed.
        if isConnected:
            if self.startPoint().isEqualTo(self.endPoint()):
                self.isClosed = True

        return isConnected
        

def toInches(centimeterValue):
    #return '{0:.4f}'.format(centimeterValue / 2.54)
    #return '{0:.4f}'.format(centimeterValue * 10)
    return '{0:.4f}'.format(centimeterValue* 10)


# Event handler for the New Seat command created event.
class NewSeatCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        import os
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        
        modelFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'models/Stool.f3d')
        
        impOptions = _app.importManager.createFusionArchiveImportOptions(modelFile)
        newDoc = _app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        des = newDoc.products.itemByProductType('DesignProductType')
        _app.importManager.importToTarget(impOptions, des.rootComponent)            
        


#******************* Sin Curve ***********************************************

# Event handler for the mesh design command created event.
class SinCurveDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            
            # Connect to the execute preview event.
            onExecutePreview = SinCurveDesignCommandExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            _handlers.append(onExecutePreview)
    
            # Create the command inputs.        
            inputs = cmd.commandInputs
            
            frequencySliderInput = inputs.addIntegerSliderCommandInput('frequency', 'Frequency', 1, 10, False)
            frequencySliderInput.valueOne = 4
            
            amplitudeSliderInput = inputs.addIntegerSliderCommandInput('amplitude', 'Amplitude', 1, 100, False)
            amplitudeSliderInput.valueOne = 40

            offsetInput = inputs.addIntegerSliderCommandInput('yOffset', 'Offset', 1, 100, False)
            offsetInput.valueOne = 50
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        
# Event handler for the execute preview event.
#def sinCurve(sketch, amplitude, frequency, yOffset):
class SinCurveDesignCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            eventArgs.isValidResult = True
    
            # Get the current values from the dialog.
            inputs = eventArgs.command.commandInputs
            
            frequency = inputs.itemById('frequency').valueOne 
            amplitude = (inputs.itemById('amplitude').valueOne * 0.01)
            amplitude = amplitude * (_seatWidth * 0.5)
            yOffset = (inputs.itemById('yOffset').valueOne * 0.01) * _seatWidth 
    
            des = adsk.fusion.Design.cast(_app.activeProduct)
            sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
            sk.areProfilesShown = False
            sk.name = 'Sin Curve (Cut)'
            
            x = 0
            angle = 0
            pntsPerFrequency = 4
            pnts = adsk.core.ObjectCollection.create()
            for i in range(0, frequency):
                for j in range(0, pntsPerFrequency):
                    y = math.sin(angle)
                    y = (y * amplitude) + yOffset
                    angle += math.pi/(pntsPerFrequency/2)
                    pnts.add(adsk.core.Point3D.create(y,x,0))
                    x += _seatHeight / (frequency * pntsPerFrequency)
        
            y = math.sin(angle)
            y = (y * amplitude) + yOffset
            pnts.add(adsk.core.Point3D.create(y,x,0))
                    
            sk.sketchCurves.sketchFittedSplines.add(pnts) 
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



#************** Patterned polygons Seat Design ********************************
# Event handler for the mesh design command created event.
class PatternedPolygonDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            
            # Connect to the execute preview event.
            onExecutePreview = PatternedPolygonDesignCommandExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            _handlers.append(onExecutePreview)
    
            # Create the command inputs.        
            inputs = cmd.commandInputs
            
            junk = inputs.addSelectionInput('junk', 'Select test', 'Select something')
            junk.isEnabled = False
            
            yNumSliderInput = inputs.addIntegerSliderCommandInput('numY', 'Width grids', 2, 20, False)
            yNumSliderInput.valueOne = 8
            yNumSliderInput.isEnabled = False
            
            xNumSliderInput = inputs.addIntegerSliderCommandInput('numX', 'Height grids', 2, 10, False)
            xNumSliderInput.valueOne = 4
            xNumSliderInput.isEnabled = False
            
            isRandomOrientation = inputs.addBoolValueInput('isRandomOrientation', 'Random orientation', True, '', True)
            isRandomOrientation.isEnabled = False
            
            angleInput = inputs.addValueInput('angleValue', 'Angle', 'deg', 0)
            #angleInput.isVisible = False
            angleInput.isEnabled = False
            
            
            isRandom = inputs.addBoolValueInput('isRandom', 'Random position', True, '', True)
    
            des = adsk.fusion.Design.cast(_app.activeProduct)
            widthAttrib = des.attributes.itemByName('adsk-Stool', 'BorderWidth')
            if widthAttrib:
                border = float(widthAttrib.value)
            else:
                border = 0                
            borderValInput = inputs.addValueInput('borderSize', 'Border', des.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(border))
            borderValInput.isVisible = False
            
            regen = inputs.addBoolValueInput('regen', 'Randomize', False, 'resources/regen', False)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        
# Event handler for the execute preview event.
class PatternedPolygonDesignCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        eventArgs.isValidResult = True

        # Get the current values from the dialog.
        inputs = eventArgs.command.commandInputs
        borderSize = inputs.itemById('borderSize').value
        
        yNum = inputs.itemById('numY').valueOne
        xNum = inputs.itemById('numX').valueOne
        
        maintainEdges = inputs.itemById('maintainEdges').value
        isRandom = inputs.itemById('isRandom').value
    
        # Create a new sketch.
        des = adsk.fusion.Design.cast(_app.activeProduct)
        sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
        sk.areProfilesShown = False
        sk.name = 'Mesh (Cut)'
        sk.isComputeDeferred = True

        random.seed()
        widthSize = (_seatWidth - (borderSize * 2))/xNum 
        heightSize = (_seatHeight - (borderSize * 2))/yNum 
    
        points = [[0 for x in range(xNum+1)] for x in range(yNum+1)] 
        for yPnt in range(0, yNum+1):
            for xPnt in range(0, xNum+1):
                x = xPnt * widthSize
                y = yPnt * heightSize
                if isRandom:
                    x =  x + (random.random() * (widthSize * (2/3))) - (widthSize * (1/3)) + borderSize
                    y =  y + (random.random() * (heightSize * (2/3))) - (heightSize * (1/3)) + borderSize
                points[yPnt][xPnt] = adsk.core.Point3D.create(x,y,0)
    
        # Fix the edge points, if needed.
        if maintainEdges:
            for xPnt in range(0, xNum+1):
                points[0][xPnt].y = borderSize - 0.5
    
            for xPnt in range(0, xNum+1):
                points[yNum][xPnt].y = _seatHeight - borderSize + 0.5
    
            for yPnt in range(0, yNum+1):
                points[yPnt][0].x = borderSize - 0.5
    
            for yPnt in range(0, yNum+1):
                points[yPnt][xNum].x = _seatWidth - borderSize + 0.5 
 
        stepInc = -1
        lines = sk.sketchCurves.sketchLines
        for yIndex in range(1, yNum):
            stepInc = -stepInc
            lastPnt = None
            
            if stepInc == 1:
                startVal = 0
                endVal = xNum+1
            else:
                startVal = xNum
                endVal = -1
                
            for xIndex in range(startVal, endVal, stepInc):
                if not lastPnt:
                    lastPnt = points[yIndex][xIndex]
                else:
                    newLine = lines.addByTwoPoints(lastPnt, points[yIndex][xIndex])
                    lastPnt = newLine.endSketchPoint

        stepInc = -1
        for xIndex in range(1, xNum):
            stepInc = -stepInc
            lastPnt = None
            
            if stepInc == 1:
                startVal = 0
                endVal = yNum+1
            else:
                startVal = yNum
                endVal = -1
                
            for yIndex in range(startVal, endVal, stepInc):
                if not lastPnt:
                    lastPnt = points[yIndex][xIndex]
                else:
                    newLine = lines.addByTwoPoints(lastPnt, points[yIndex][xIndex])
                    lastPnt = newLine.endSketchPoint

#****************** Mesh Seat Design ******************************************

# Event handler for the mesh design command created event.
class MeshDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command
        
        # Connect to the execute preview event.
        onExecutePreview = MeshDesignCommandExecutePreviewHandler()
        cmd.executePreview.add(onExecutePreview)
        _handlers.append(onExecutePreview)

        # Create the command inputs.        
        inputs = cmd.commandInputs
        
        yNumSliderInput = inputs.addIntegerSliderCommandInput('numY', 'Width grids', 2, 20, False)
        yNumSliderInput.valueOne = 8
        
        xNumSliderInput = inputs.addIntegerSliderCommandInput('numX', 'Height grids', 2, 10, False)
        xNumSliderInput.valueOne = 4
        
        maintainEdges = inputs.addBoolValueInput('maintainEdges', 'Straight edges', True, '', True)
        maintainEdges.isVisible = False
        
        isRandom = inputs.addBoolValueInput('isRandom', 'Random position', True, '', True)

        des = adsk.fusion.Design.cast(_app.activeProduct)
        widthAttrib = des.attributes.itemByName('adsk-Stool', 'BorderWidth')
        if widthAttrib:
            border = float(widthAttrib.value)
        else:
            border = 0                
        borderValInput = inputs.addValueInput('borderSize', 'Border', des.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(border))
        borderValInput.isVisible = False
        
        regen = inputs.addBoolValueInput('regen', 'Randomize', False, 'resources/regen', False)

        
# Event handler for the execute preview event.
class MeshDesignCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        eventArgs.isValidResult = True

        # Get the current values from the dialog.
        inputs = eventArgs.command.commandInputs
        borderSize = inputs.itemById('borderSize').value
        
        yNum = inputs.itemById('numY').valueOne
        xNum = inputs.itemById('numX').valueOne
        
        maintainEdges = inputs.itemById('maintainEdges').value
        isRandom = inputs.itemById('isRandom').value
    
        # Create a new sketch.
        des = adsk.fusion.Design.cast(_app.activeProduct)
        sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
        sk.areProfilesShown = False
        sk.name = 'Mesh (Cut)'
        sk.attributes.add('adsk-Seat', 'SeatSketch', '')
        sk.isComputeDeferred = True

        random.seed()
        widthSize = (_seatWidth - (borderSize * 2))/xNum 
        heightSize = (_seatHeight - (borderSize * 2))/yNum 
    
        points = [[0 for x in range(xNum+1)] for x in range(yNum+1)] 
        for yPnt in range(0, yNum+1):
            for xPnt in range(0, xNum+1):
                x = xPnt * widthSize
                y = yPnt * heightSize
                if isRandom:
                    x =  x + (random.random() * (widthSize * (2/3))) - (widthSize * (1/3)) + borderSize
                    y =  y + (random.random() * (heightSize * (2/3))) - (heightSize * (1/3)) + borderSize
                points[yPnt][xPnt] = adsk.core.Point3D.create(x,y,0)
    
        # Fix the edge points, if needed.
        if maintainEdges:
            for xPnt in range(0, xNum+1):
                points[0][xPnt].y = borderSize - 0.5
    
            for xPnt in range(0, xNum+1):
                points[yNum][xPnt].y = _seatHeight - borderSize + 0.5
    
            for yPnt in range(0, yNum+1):
                points[yPnt][0].x = borderSize - 0.5
    
            for yPnt in range(0, yNum+1):
                points[yPnt][xNum].x = _seatWidth - borderSize + 0.5 
 
        stepInc = -1
        lines = sk.sketchCurves.sketchLines
        for yIndex in range(1, yNum):
            stepInc = -stepInc
            lastPnt = None
            
            if stepInc == 1:
                startVal = 0
                endVal = xNum+1
            else:
                startVal = xNum
                endVal = -1
                
            for xIndex in range(startVal, endVal, stepInc):
                if not lastPnt:
                    lastPnt = points[yIndex][xIndex]
                else:
                    newLine = lines.addByTwoPoints(lastPnt, points[yIndex][xIndex])
                    lastPnt = newLine.endSketchPoint

        stepInc = -1
        for xIndex in range(1, xNum):
            stepInc = -stepInc
            lastPnt = None
            
            if stepInc == 1:
                startVal = 0
                endVal = yNum+1
            else:
                startVal = yNum
                endVal = -1
                
            for yIndex in range(startVal, endVal, stepInc):
                if not lastPnt:
                    lastPnt = points[yIndex][xIndex]
                else:
                    newLine = lines.addByTwoPoints(lastPnt, points[yIndex][xIndex])
                    lastPnt = newLine.endSketchPoint
                    
                       
#        for yPnt in range(0, heightNum):
#            for xPnt in range(0, widthNum):
#                lines.addByTwoPoints(points[yPnt][xPnt], points[yPnt][xPnt+1])
#                lines.addByTwoPoints(points[yPnt][xPnt], points[yPnt+1][xPnt])
#                
#        for xPnt in range(0, widthNum):
#            lines.addByTwoPoints(points[heightNum][xPnt], points[heightNum][xPnt+1])
#    
#        for yPnt in range(0, heightNum):
#            lines.addByTwoPoints(points[yPnt][widthNum], points[yPnt+1][widthNum])        


#****************** Flower Seat Design ****************************************

# Event handler for the mesh design command created event.
class FlowerDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Connect to the execute preview event.
        onExecutePreview = FlowerDesignCommandExecutePreviewHandler()
        cmd.executePreview.add(onExecutePreview)
        _handlers.append(onExecutePreview)
        
        # Connect to the input changed event.
        onInputChanged = FlowerDesignInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        _handlers.append(onInputChanged)        
        
        # Get the previous values as the default.
        des = adsk.fusion.Design.cast(_app.activeProduct)
        attrib = des.attributes.itemByName('adsk-Stool', 'FlowerDefaults')
        if attrib:
            val = eval(attrib.value)
            petalSides = int(val['petalSides'])
            petalSize = int(val['petalSize'])
            petalWidthCenter = int(val['petalYPos'])
            petalHeightCenter = int(val['petalXPos'])
            petalCount = int(val['petalCount'])
            petalWidthOffset = 0    # int(val['petalYOffset'])            
            petalHeightOffset = 0   #int(val['petalXOffset'])
        else:
            petalSides = 5
            petalSize = 25
            petalWidthCenter = 50
            petalHeightCenter = 50
            petalCount = 5
            petalWidthOffset = 0
            petalHeightOffset = 0          
        
        inputs = cmd.commandInputs
        petalSidesInput = inputs.addIntegerSliderCommandInput('petalSides', 'Petal sides', 3, 10, False)
        petalSidesInput.valueOne = petalSides

        petalSizeInput = inputs.addIntegerSliderCommandInput('petalSize', 'Petal size', 1, 100, False)
        petalSizeInput.valueOne = petalSize
        
        petalWidthCenterInput = inputs.addIntegerSliderCommandInput('petalWidthCenter', 'Flower center X', 1, 100, False)
        petalWidthCenterInput.valueOne = petalWidthCenter
        
        petalHeightCenterInput = inputs.addIntegerSliderCommandInput('petalHeightCenter', 'Flower center Y', 1, 100, False)
        petalHeightCenterInput.valueOne = petalHeightCenter
        
        petalCountInput = inputs.addIntegerSliderCommandInput('petalCount', 'Petal count', 3, 20, False)
        petalCountInput.valueOne = petalCount

        petalCenterWidthOffsetInput = inputs.addIntegerSliderCommandInput('petalWidthPosition', 'Width position', 0, 100, False)
        petalCenterWidthOffsetInput.valueOne = petalWidthOffset

        petalCenterHeightOffsetInput = inputs.addIntegerSliderCommandInput('petalHeightPosition', 'Height position', 0, 100, False)
        petalCenterHeightOffsetInput.valueOne = petalHeightOffset

        resetInput = inputs.addBoolValueInput('reset', 'Reset to default', False, 'resources/regen', False)


class FlowerDesignInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        inputs = eventArgs.inputs
        
        if eventArgs.input.id == 'reset':
            petalSidesInput = inputs.itemById('petalSides')
            petalSidesInput.ValueOne = 5
            
            petalSizeInput = inputs.itemById('petalSize')
            petalSizeInput.ValueOne = 25
            
            petalWidthCenterInput = inputs.itemById('petalWidthCenter')
            petalWidthCenterInput.valueOne = 50

            petalHeightCenterInput = inputs.itemById('petalHeightCenter')
            petalHeightCenterInput.valueOne = 50
            
            petalCountInput = inputs.itemById('petalCount')
            petalCountInput.valueOne = 5
            
            petalCenterWidthOffsetInput = inputs.itemById('petalWidthPosition')
            petalCenterWidthOffsetInput.valueOne = 0

            petalCenterHeightOffsetInput = inputs.itemById('petalHeightPosition')
            petalCenterHeightOffsetInput.valueOne = 0


# Event handler for the execute preview event.
class FlowerDesignCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            eventArgs.isValidResult = True
            
            inputs = eventArgs.command.commandInputs
    
            petalSides = inputs.itemById('petalSides').valueOne
            
            petalSizeRatio = inputs.itemById('petalSize').valueOne * 0.01
            maxSize = _seatWidth * 0.4
            minSize = 2
            petalSize = (maxSize - minSize) * petalSizeRatio + minSize
            petalSize = petalSize / 2.0
    
            petalYCenterRatio = inputs.itemById('petalHeightCenter').valueOne * 0.01
            minOffset = -petalSize
            maxOffset = petalSize
            yPetalCenterOffset = (maxOffset - minOffset) * petalYCenterRatio + minOffset
    
            petalXCenterRatio = inputs.itemById('petalWidthCenter').valueOne * 0.01
            minOffset = -petalSize
            maxOffset = petalSize
            xPetalCenterOffset = (maxOffset - minOffset) * petalXCenterRatio + minOffset
            
            petalCount = inputs.itemById('petalCount').valueOne
            
            maxXPos = _seatWidth - (petalSize * 2.5)
            minXPos = petalSize * 2.5
            petalXPosRatio = inputs.itemById('petalHeightPosition').valueOne * 0.01
            xOffset = (maxXPos - minXPos) * petalXPosRatio + minXPos
            
            maxYPos = _seatHeight - (petalSize * 2.5)
            minYPos = petalSize * 2.5
            petalYPosRatio = inputs.itemById('petalWidthPosition').valueOne * 0.01
            yOffset = (maxYPos - minYPos) * petalYPosRatio + minYPos
            
            # Create a new sketch.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
            sk.areProfilesShown = False
            sk.name = 'Flower (Cut)'
            sk.isComputeDeferred = True

            # Save values in an attribute.
            values = {'petalSides': str(petalSides), 'petalSize': str(int(petalSizeRatio * 100)), 'petalYPos' : str(int(petalXCenterRatio * 100)) , 'petalXPos' : str(int(petalYCenterRatio * 100)), 'petalCount' : str(petalCount), 'petalXOffset' : str(int(petalXPosRatio * 100)), 'petalYOffset' : str(int(petalYPosRatio * 100))}
            des.attributes.add('adsk-Stool', 'FlowerDefaults', str(values))
         
             # Create the initial polygon where the starting "point" is at (0,0).
            polys = []
            poly = []
            for i in range(0, petalSides):
                angle = i * ((math.pi*2)/petalSides)
                x = (petalSize * math.cos(angle)) - petalSize + yPetalCenterOffset
                y = (petalSize * math.sin(angle)) + xPetalCenterOffset
                poly.append(adsk.core.Point3D.create(x, y, 0))
            polys.append(poly)
            
            # Create the rotated copies.
            for i in range(1, petalCount):
                angle = i * ((math.pi*2)/petalCount)
                mat = adsk.core.Matrix3D.create()
                mat.setToRotation(angle, adsk.core.Vector3D.create(0,0,1), adsk.core.Point3D.create(0,0,0))
                poly = []        
                for j in range(0, petalSides):
                    pnt = adsk.core.Point3D.cast(polys[0][j]).copy()
                    pnt.transformBy(mat)
                    pnt.x += xOffset
                    pnt.y += yOffset
                    poly.append(pnt)
                    
                polys.append(poly)
    
            # Reposition the initial polygon.
            for i in range(0, petalSides):
                polys[0][i].x += xOffset
                polys[0][i].y += yOffset
        
            lines = adsk.fusion.SketchLines.cast(sk.sketchCurves.sketchLines)
            for i in range(0, petalCount):
                poly = polys[i]
        
                startLine = None
                lastLine = None
                for j in range(1, petalSides):
                    if not lastLine:
                        lastLine = lines.addByTwoPoints(poly[j-1], poly[j])
                    else:
                        lastLine = lines.addByTwoPoints(lastLine.endSketchPoint, poly[j])
                        
                    if not startLine:
                        startLine = lastLine
                        
                lines.addByTwoPoints(lastLine.endSketchPoint, startLine.startSketchPoint)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


#****************** Circles Seat Design ***************************************

# Event handler for the mesh design command created event.
class CirclesDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
    
            # Connect to the execute preview event.
            onExecutePreview = CirclesDesignCommandExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            _handlers.append(onExecutePreview)        
    
            # Create the command inputs.        
            inputs = cmd.commandInputs
            
            numCirclesIntSliderInput = inputs.addIntegerSliderCommandInput('numCircles', 'Max number', 1, 30, False)
            numCirclesIntSliderInput.valueOne = 10

            des = adsk.fusion.Design.cast(_app.activeProduct)
            maxSizeIntSliderInput = inputs.addIntegerSliderCommandInput('maxSize', 'Max size', 1, 100, False)
            maxSizeIntSliderInput.valueOne = 75
            
            des = adsk.fusion.Design.cast(_app.activeProduct)
            widthAttrib = des.attributes.itemByName('adsk-Stool', 'BorderWidth')
            if widthAttrib:
                border = float(widthAttrib.value)
            else:
                border = 0                
            borderValInput = inputs.addValueInput('borderSize', 'Border', des.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(border))

            overlap = inputs.addBoolValueInput('allowOverlap', 'Allow overlap', True, '', False)
            
            regen = inputs.addBoolValueInput('regen', 'Randomize', False, 'resources/regen', False)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        
# Event handler for the execute preview event.
class CirclesDesignCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        sk = None
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            eventArgs.isValidResult = True
            
            # Get the current values from the dialog.
            inputs = eventArgs.command.commandInputs
            numCirclesInput = inputs.itemById('numCircles')
            numCircles = numCirclesInput.valueOne

            maxSizeInput = inputs.itemById('maxSize') 
            maxSize = maxSizeInput.valueOne * 0.01
            minVal = 2
            maxVal = _seatWidth * 0.8
            maxDia = (maxVal * maxSize) + minVal
            
            borderWidth = inputs.itemById('borderSize').value
            
            allowOverlap = inputs.itemById('allowOverlap').value
        
            # Create a new sketch.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
            sk.areProfilesShown = False
            sk.name = 'Circles (Cut)'
            sk.isComputeDeferred = True
    
            # Save the width to use as the default for all stool commands.
            des.attributes.add('adsk-Stool', 'BorderWidth', str(borderWidth))
            
            circs = sk.sketchCurves.sketchCircles
    
            random.seed()
        
            circles = []
            for i in range(0, numCircles):
                isOk = False
                tryCount = 0
                while not isOk:
                    if tryCount > 50:
                        isOk = True
                    else:
                        tryCount += 1
                        newDia = random.random() * (maxDia - _minSize) + _minSize
                
                        x = (random.random() * (_seatWidth - newDia - (borderWidth*2))) + borderWidth + (newDia/2.0)
                        y = (random.random() * (_seatHeight - newDia - (borderWidth*2))) + borderWidth + (newDia/2.0)
                    
                        if not allowOverlap:
                            center = adsk.core.Point3D.create(x,y,0)
                            
                            overlap = False
                            for circ in circles:
                                if circ.center.distanceTo(center) <= circ.radius + (newDia/2) + borderWidth:
                                    overlap = True
                                    break
                                    
                            if not overlap:
                                isOk = True
                        else:
                            isOk = True
        
                if tryCount <= 50:
                    skCircle = circs.addByCenterRadius(adsk.core.Point3D.create(x,y,0), newDia/2)
                    circles.append(skCircle.geometry)
                else:
                    break                       
            sk.isComputeDeferred = False
        except:
            if sk:
                sk.isComputeDeferred = False
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


#****************** Circles Seat Design ***************************************

# Event handler for the mesh design command created event.
class RectanglesDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
    
            # Connect to the execute preview event.
            onExecutePreview = RectanglesDesignCommandExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            _handlers.append(onExecutePreview)        
    
            # Create the command inputs.        
            inputs = cmd.commandInputs
            
            numCirclesIntSliderInput = inputs.addIntegerSliderCommandInput('numRectangles', 'Max number', 1, 20, False)
            numCirclesIntSliderInput.valueOne = 10
            
            des = adsk.fusion.Design.cast(_app.activeProduct)
            widthAttrib = des.attributes.itemByName('adsk-Stool', 'BorderWidth')
            if widthAttrib:
                border = float(widthAttrib.value)
            else:
                border = 0          
            borderValInput = inputs.addValueInput('borderSize', 'Border', des.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(border))
 
            overlap = inputs.addBoolValueInput('allowOverlap', 'Allow overlap', True, '', False)
           
            regen = inputs.addBoolValueInput('regen', 'Randomize', False, 'resources/regen', False)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        
# Event handler for the execute preview event.
class RectanglesDesignCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        sk = None
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            eventArgs.isValidResult = True
            
            # Get the current values from the dialog.
            inputs = eventArgs.command.commandInputs
            numRectanglesInput = inputs.itemById('numRectangles')
            numRectangles = numRectanglesInput.valueOne
            
            borderWidth = inputs.itemById('borderSize').value

            allowOverlap = inputs.itemById('allowOverlap').value
        
            # Create a new sketch.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
            sk.areProfilesShown = False
            sk.name = 'Rectangles (Cut)'
            sk.isComputeDeferred = True
    
            # Save the width to use as the default for all stool commands.
            des.attributes.add('adsk-Stool', 'BorderWidth', str(borderWidth))
            
            lines = sk.sketchCurves.sketchLines
    
            random.seed()
    
            rects = []
            for i in range(0, numRectangles):
                isOk = False
                while not isOk:
                    newWidth = random.random() * (_seatWidth / 4)
                    if newWidth < _minSize:
                        newWidth = _minSize
                            
                    newHeight = random.random() * (_seatHeight / 2)
                    if newHeight < _minSize:
                        newHeight = _minSize
        
                    x = (random.random() * (_seatWidth - newWidth - (borderWidth*2))) + borderWidth
                    y = (random.random() * (_seatHeight - newHeight - (borderWidth*2))) + borderWidth
        
                    if not allowOverlap:
                        newRect = adsk.core.BoundingBox2D.create(adsk.core.Point2D.create(x,y), adsk.core.Point2D.create(x+newWidth, y+newHeight))
                        
                        overlap = False
                        for rect in rects:
                            if newRect.intersects(rect):
                                overlap = True
                                break
                                
                        if not overlap:
                            rects.append(newRect)
                            isOk = True
                    else:
                        isOk = True
                    
                lines.addTwoPointRectangle(adsk.core.Point3D.create(x,y,0), adsk.core.Point3D.create(x+newWidth, y+newHeight, 0))

            sk.isComputeDeferred = False
        except:
            if sk:
                sk.isComputeDeferred = False
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


#***************** Main add-in functionality **********************************

def run(context):
    try:
        # Create the command definitions and connect to the command created event.
        newSeatCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-NewSeat', 'New Seat', 'Create a new seat design.', 'resources/NewSeat')
        newSeatCmdDef.toolClipFilename = 'resources/newStoolToolclip.png'
        newSeatCommandCreated = NewSeatCommandCreatedHandler()
        newSeatCmdDef.commandCreated.add(newSeatCommandCreated)
        _handlers.append(newSeatCommandCreated)

        cutSeatCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-CutSeat', 'Cut Seat', 'Send the design to the NC Mill.', 'resources/CutSeat')
        cutSeatCmdDef.toolClipFilename = 'resources/sendToTool.png'
        cutSeatCommandCreated = CutSeatCommandCreatedHandler()
        cutSeatCmdDef.commandCreated.add(cutSeatCommandCreated)
        _handlers.append(cutSeatCommandCreated) 

        meshDesignCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-MeshDesign', 'Mesh', 'Create a random mesh seat design.', 'resources/MeshDesign')
        meshDesignCmdDef.toolClipFilename = 'resources/meshToolclip.png'
        meshDesignCommandCreated = MeshDesignCommandCreatedHandler()
        meshDesignCmdDef.commandCreated.add(meshDesignCommandCreated)
        _handlers.append(meshDesignCommandCreated)
        
        flowerDesignCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-FlowerDesign', 'Flower', 'Create a flower seat design.', 'resources/FlowerDesign')
        flowerDesignCmdDef.toolClipFilename = 'resources/flowerToolclip.png'
        flowerDesignCommandCreated = FlowerDesignCommandCreatedHandler()
        flowerDesignCmdDef.commandCreated.add(flowerDesignCommandCreated)
        _handlers.append(flowerDesignCommandCreated)

        circlesDesignCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-CirclesDesign', 'Circles', 'Create random circles seat design.', 'resources/CirclesDesign')
        circlesDesignCmdDef.toolClipFilename = 'resources/circlesToolclip.png'
        circlesDesignCommandCreated = CirclesDesignCommandCreatedHandler()
        circlesDesignCmdDef.commandCreated.add(circlesDesignCommandCreated)
        _handlers.append(circlesDesignCommandCreated)

        rectanglesDesignCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-RectanglesDesign', 'Rectangles', 'Create random rectangles seat design.', 'resources/RectanglesDesign')
        rectanglesDesignCmdDef.toolClipFilename = 'resources/rectanglesToolclip.png'
        rectanglesDesignCommandCreated = RectanglesDesignCommandCreatedHandler()
        rectanglesDesignCmdDef.commandCreated.add(rectanglesDesignCommandCreated)
        _handlers.append(rectanglesDesignCommandCreated)

        sinCurveDesignCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-SinCurveDesign', 'Sin Curve', 'Create a sin curve seat design.', 'resources/SinCurveDesign')
        sinCurveDesignCmdDef.toolClipFilename = 'resources/sinToolclip.png'
        sinCurveDesignCommandCreated = SinCurveDesignCommandCreatedHandler()
        sinCurveDesignCmdDef.commandCreated.add(sinCurveDesignCommandCreated)
        _handlers.append(sinCurveDesignCommandCreated)

#        patternedPolygonDesignCmdDef = _ui.commandDefinitions.addButtonDefinition('adsk-PatternedPolygonDesign', 'Polygons', 'Create random rectangles seat design.', 'resources/RectanglesDesign')
#        patternedPolygonDesignCmdDef.toolClipFilename = 'resources/rectanglesToolclip.png'
#        patternedPolygonDesignCommandCreated = PatternedPolygonDesignCommandCreatedHandler()
#        patternedPolygonDesignCmdDef.commandCreated.add(patternedPolygonDesignCommandCreated)
#        _handlers.append(patternedPolygonDesignCommandCreated)
        
        # Get the MODEL workspace.
        modelWS = _ui.workspaces.itemById('FusionSolidEnvironment')
        
        # Add a new panel.
        seatPanel = modelWS.toolbarPanels.add('adsk-SeatPanel', 'Stool Design')
        
        # Add the buttons to the panel.
        newCtrl = seatPanel.controls.addCommand(newSeatCmdDef)
        newCtrl.isPromotedByDefault = True
        newCtrl.isPromoted = True
        
        meshCtrl = seatPanel.controls.addCommand(meshDesignCmdDef)
        meshCtrl.isPromoted = True
        flowerCtrl = seatPanel.controls.addCommand(flowerDesignCmdDef)
        flowerCtrl.isPromoted = True
        circlesCtrl = seatPanel.controls.addCommand(circlesDesignCmdDef)
        circlesCtrl.isPromoted = True
        rectanglesCtrl = seatPanel.controls.addCommand(rectanglesDesignCmdDef)
        rectanglesCtrl.isPromoted = True
        sinCurveCtrl = seatPanel.controls.addCommand(sinCurveDesignCmdDef)
        sinCurveCtrl.isPromoted = True
        cutCtrl = seatPanel.controls.addCommand(cutSeatCmdDef)
        cutCtrl.isPromoted = True
        
#        polygonCtrl = seatPanel.controls.addCommand(patternedPolygonDesignCmdDef)
#        polygonCtrl.isPromoted = True
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        # Clean up the UI.
        seatPanel = _ui.allToolbarPanels.itemById('adsk-SeatPanel')
        if seatPanel:
            seatPanel.deleteMe()

        newSeatCmdDef = _ui.commandDefinitions.itemById('adsk-NewSeat')
        if newSeatCmdDef:
            newSeatCmdDef.deleteMe()
    
        cutSeatCmdDef = _ui.commandDefinitions.itemById('adsk-CutSeat')
        if cutSeatCmdDef:
            cutSeatCmdDef.deleteMe()

        meshDesignCmdDef = _ui.commandDefinitions.itemById('adsk-MeshDesign')
        if meshDesignCmdDef:
            meshDesignCmdDef.deleteMe()
            
        flowerDesignCmdDef = _ui.commandDefinitions.itemById('adsk-FlowerDesign')
        if flowerDesignCmdDef:
            flowerDesignCmdDef.deleteMe()
        
        circlesDesignCmdDef = _ui.commandDefinitions.itemById('adsk-CirclesDesign')
        if circlesDesignCmdDef:
            circlesDesignCmdDef.deleteMe()

        rectanglesDesignCmdDef = _ui.commandDefinitions.itemById('adsk-RectanglesDesign')
        if rectanglesDesignCmdDef:
            rectanglesDesignCmdDef.deleteMe()

        sinCurveDesignCmdDef = _ui.commandDefinitions.itemById('adsk-SinCurveDesign')
        if sinCurveDesignCmdDef:
            sinCurveDesignCmdDef.deleteMe()

#        patternedPolygonDesignCmdDef = _ui.commandDefinitions.itemById('adsk-PatternedPolygonDesign')
#        if patternedPolygonDesignCmdDef:
#            patternedPolygonDesignCmdDef.deleteMe()
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
