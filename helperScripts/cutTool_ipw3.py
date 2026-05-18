#!/usr/bin/python3
import sys,os
from math import *
import argparse
import subprocess as sp
import numpy as np
from enum import Enum
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
import tecplot

############################
def line_intersect(Ax1, Ay1, Ax2, Ay2, Bx1, By1, Bx2, By2):
    """ returns a (x, y) tuple or None if there is no intersection """
    d = (By2 - By1) * (Ax2 - Ax1) - (Bx2 - Bx1) * (Ay2 - Ay1)
    if d:
        uA = ((Bx2 - Bx1) * (Ay1 - By1) - (By2 - By1) * (Ax1 - Bx1)) / d
        uB = ((Ax2 - Ax1) * (Ay1 - By1) - (Ay2 - Ay1) * (Ax1 - Bx1)) / d
    else:
        return (False,None)
    # if not(0.0 <= uA <= 1.0 and 0.0 <= uB <= 1.0):
    #    return (False,None)

    x = Ax1 + uA * (Ax2 - Ax1)
    y = Ay1 + uA * (Ay2 - Ay1)

    return True,(x, y)

############################
def define_circle(p1, p2, p3):
    """
    Returns the center and radius of the circle passing the given 3 points.
    In case the 3 points form a line, returns (None, infinity).
    """
    temp = p2[0] * p2[0] + p2[1] * p2[1]
    bc = (p1[0] * p1[0] + p1[1] * p1[1] - temp) / 2
    cd = (temp - p3[0] * p3[0] - p3[1] * p3[1]) / 2
    det = (p1[0] - p2[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p2[1])

    if abs(det) < 1.0e-12:
        cx = (p1[0] + p2[0] + p3[0]) / 3.0
        cy = (p1[1] + p2[1] + p3[1]) / 3.0
        radius = 0.5*sqrt((p3[0]-p1[0])*(p3[0]-p1[0])+(p3[1]-p1[1])*(p3[1]-p1[1]))

        return (cx, cy, radius)

    # Center of circle
    cx = (bc*(p2[1] - p3[1]) - cd*(p1[1] - p2[1])) / det
    cy = ((p1[0] - p2[0]) * cd - (p2[0] - p3[0]) * bc) / det

    radius = np.sqrt((cx - p1[0])**2 + (cy - p1[1])**2)
    return (cx, cy, radius)

############################
def ErrorQuit(message):
    print ('Error:',message)
    exit(0)

############################
class Slice(object):
    """docstring for Slice"""
    def __init__(self, zone, tecplotDataSet, normal, position, chord, axis, rotationAngle, highlight, requestOrdering, initialDataRank, cleanSlice):
        self.tecplotdataset = tecplotDataSet
        self.zone = zone
        self.normal = normal
        self.axis = axis
        self.rotationAngle = rotationAngle
        self.highlightRef = highlight
        self.cleanSlice = cleanSlice
        self.isCGNS = tecplotDataSet.isCGNS
        self.initialDataRank = initialDataRank
        self.requestOrdering = requestOrdering

        self.isOrdered = (self.zone.zone_type == tecplot.constant.ZoneType.Ordered)

        if (axis == 'y'):
            self.verticalID = 2
            self.spanID = 1
        elif (axis == 'z'):
            self.verticalID = 1
            self.spanID = 2
        else:
            ErrorQuit("Wrong axis!")

        x = self.getVariable(0);
        y = self.getVariable(self.verticalID);
        z = self.getVariable(self.spanID);

        xIce = None
        yIce = None
        zIce = None
        self.iceCoordExists = False

        for v in range(self.getNumberOfVariables()):
            if "x_ice" in self.tecplotdataset.getVariableName(variable=v).lower():
                self.iceCoordExists = True
                self.xIcedID = v
                xIce = self.getVariable(self.xIcedID)
                yIce = self.getVariable(self.xIcedID+self.verticalID)
                zIce = self.getVariable(self.xIcedID+self.spanID)

        self.lowerHornHeight    = 0.0
        self.lowerHornAngle     = 0.0
        self.upperHornHeight    = 0.0
        self.upperHornAngle     = 0.0
        self.iceMass            = 0.0

        # Rotation of cut if required
        nNodes = len(x)
        if abs(rotationAngle) > 0.0:
            cosA = cos(rotationAngle*pi/180.0)
            sinA = sin(rotationAngle*pi/180.0)

            newHLRefX = self.highlightRef[0]*cosA - self.highlightRef[self.verticalID]*sinA
            newHLRefY = self.highlightRef[0]*sinA + self.highlightRef[self.verticalID]*cosA
            self.highlightRef[0] = newHLRefX
            self.highlightRef[self.verticalID] = newHLRefY

            for nodeI in range(nNodes):
                newX = x[nodeI]*cosA - y[nodeI]*sinA
                newY = x[nodeI]*sinA + y[nodeI]*cosA
                x[nodeI] = newX
                y[nodeI] = newY

            if self.iceCoordExists:
                for nodeI in range(nNodes):
                    newX = xIce[nodeI]*cosA - yIce[nodeI]*sinA
                    newY = xIce[nodeI]*sinA + yIce[nodeI]*cosA
                    xIce[nodeI] = newX
                    yIce[nodeI] = newY

        # Rotation around vertical axis
        cosS = self.normal[self.spanID]
        sinS = self.normal[0]
        normInv = 1.0 / (sqrt(cosS*cosS+sinS*sinS)+1.0e-20)
        cosS *= normInv
        sinS *= normInv

        newHLRefX = self.highlightRef[0]*cosS - self.highlightRef[self.spanID]*sinS
        newHLRefY = self.highlightRef[0]*sinS + self.highlightRef[self.spanID]*cosS
        self.highlightRef[0] = newHLRefX
        self.highlightRef[self.spanID] = newHLRefY

        for nodeI in range(nNodes):
            newX = x[nodeI]*cosS - z[nodeI]*sinS
            newY = x[nodeI]*sinS + z[nodeI]*cosS
            x[nodeI] = newX
            z[nodeI] = newY

        if self.iceCoordExists:
            for nodeI in range(nNodes):
                newX = xIce[nodeI]*cosS - zIce[nodeI]*sinS
                newY = xIce[nodeI]*sinS + zIce[nodeI]*cosS
                xIce[nodeI] = newX
                zIce[nodeI] = newY



        # Evaluating chord if not given
        xmax = x.argmax()
        if (chord == None):
            self.chord = x.max() - x.min()
        else:
            self.chord = chord

        self.position = np.array([x[xmax], y[xmax], z[xmax]])

        nodemap = self.getNodeMap()
        nElements = nodemap.shape[0]

        self.nElements = nElements
        self.nNodes = len(x)

        self.x = x
        self.y = y
        self.z = z

        if self.iceCoordExists:
            self.xIce = xIce
            self.yIce = yIce
            self.zIce = zIce
            self.sThickness = np.zeros(self.nElements+1, dtype=float)
            self.hIce = np.zeros(self.nElements+1, dtype=float)

        if self.requestOrdering:
            self.setElementConnectivity(nodemap)

            if self.iceCoordExists:
                self.computeIceThickness(nodemap)

    ############################
    def findTrailingEdge(self,nodemap):

        x = self.x;
        y = self.y;

        xmax = x.argmax()

        # Finding maximum x coordinate to build a list of candidates for TE
        xMaxPt = np.array([x[xmax],y[xmax]])
        teCandidatesList = set()
        teCandidatesList.add(xmax)

        criticalAngle = 100.0 * pi/180.0
        for nodeIndex in range(self.nNodes):
            deltaX = x[nodeIndex] - xMaxPt[0]
            if abs(deltaX) < 1.0e-3:
                deltaY = y[nodeIndex] - xMaxPt[1]
                angle = atan2(deltaY, deltaX)
                if abs(angle) < criticalAngle:
                    teCandidatesList.add(nodeIndex)

        # From list of TE candidate nodes, evaluate average position in y and z, as if all candidates are on a y-z plane
        yAvg = 0.0
        count = 0.0
        for nodeI in teCandidatesList:
            yAvg += y[nodeI]
            count += 1.0

        yAvg = yAvg / count

        # Find node at middle of y-z plane which would be the node in middle of blunt TE or on sharp TE
        nodeTE = xmax
        distMin = 1.0e6
        for nodeI in teCandidatesList:
            dist = abs(yAvg - y[nodeI])
            if dist < distMin:
                distMin = dist
                nodeTE = nodeI

        # Located TE, which shlould be in middle of blunt TE or exactly on sharp TE
        tePt = np.array([x[nodeTE],y[nodeTE]])

        # Trying to find element connected to TE from which the ordering of nodes will be started
        found = np.where(nodemap[:,0] == nodeTE)[0]
        elementIndex1 = -1
        elementIndex2 = -1
        if (len(found) < 1):
            found = np.where(nodemap[:,1] == nodeTE)[0]
            if (len(found) > 1):
                elementIndex1 = found[0]
                elementIndex2 = found[1]
            elif (len(found) == 1):
                elementIndex1 = found[0]
                elementIndex2 = elementIndex1
        else:
            elementIndex1 = found[0]
            found = np.where(nodemap[:,1] == nodeTE)[0]
            if (len(found) > 0):
                elementIndex2 = found[0]
            else:
                elementIndex2 = elementIndex1

        nodeIndex1 = -1
        nodeIndex2 = -1
        TEposInElem1 = -1
        TEposInElem2 = -1
        if (nodemap[elementIndex1,0] == nodeTE):
            nodeIndex1 = nodemap[elementIndex1,1]
            TEposInElem1 = 0
        else:
            nodeIndex1 = nodemap[elementIndex1,0]
            TEposInElem1 = 1

        if (nodemap[elementIndex2,0] == nodeTE):
            nodeIndex2 = nodemap[elementIndex2,1]
            TEposInElem2 = 0
        else:
            nodeIndex2 = nodemap[elementIndex2,0]
            TEposInElem2 = 1

        p1 = np.array([x[nodeIndex1],y[nodeIndex1]])
        p2 = np.array([x[nodeIndex2],y[nodeIndex2]])

        t1Tmp = p1 - tePt
        t1NormInv = 1.0 / (sqrt(np.sum(t1Tmp**2)) + 1.0e-10)
        tVec1 = t1Tmp*t1NormInv

        t2Tmp = p2 - tePt
        t2NormInv = 1.0 / (sqrt(np.sum(t2Tmp**2)) + 1.0e-10)
        tVec2 = t2Tmp*t2NormInv

        # Find which element is below the TE (in clockwise direction)
        elemStart = elementIndex1
        TEposInElem = TEposInElem1
        if tVec1[1] < tVec2[1]:
            elemStart = elementIndex1
            TEposInElem = TEposInElem1
        else:
            elemStart = elementIndex2
            TEposInElem = TEposInElem2

        return (tePt, nodeTE, elemStart, TEposInElem)

    ############################
    def computeHighlightFromTE(self,nodemap, tePt):
        x = self.x
        y = self.y

        # Find point which is the most distant point from TE
        dist = 1e-12
        nodeIndexMax = x.argmin()

        for nodeI in range(self.nNodes):
            pt = np.array([x[nodeI],y[nodeI]])

            diff = sqrt(np.sum((tePt-pt)**2))

            if (diff > dist):
                dist = diff
                nodeIndexMax = nodeI

        iNodeMax = self.node2OrderedNode[nodeIndexMax]
        nodeIndexLeft = self.ordered[iNodeMax-1]
        nodeIndexRight = self.ordered[iNodeMax+1]

        p1 = np.array([x[nodeIndexMax],y[nodeIndexMax]])
        p2 = np.array([x[nodeIndexLeft],y[nodeIndexLeft]])
        p3 = np.array([x[nodeIndexRight],y[nodeIndexRight]])

        (cx, cy, r) = define_circle(p1,p2,p3)

        nElement = len(nodemap)
        sHL = 0.0

        ptHL = np.array([0.0,0.0, 0.0])

        for nodeIndex in (nodeIndexLeft, nodeIndexRight):
            point = np.array([x[nodeIndex],y[nodeIndex]])

            found,pointIntersect = line_intersect(p1[0],p1[1],point[0],point[1],cx,cy,tePt[0],tePt[1])

            if (found):
                distHLTo1 = sqrt((pointIntersect[0]-p1[0])**2.0 + (pointIntersect[1]-p1[1])**2.0)
                distPtTo1 = sqrt((point[0]-p1[0])**2.0 + (point[1]-p1[1])**2.0)

                r1 = distHLTo1 / distPtTo1

                iNode = self.node2OrderedNode[nodeIndex]
                sHL = r1*self.S[iNode] + (1.0 - r1)*self.S[iNodeMax]
                ptHL[0] = pointIntersect[0]
                ptHL[1] = pointIntersect[1]

        # exit()
        return (ptHL, sHL)

    ############################
    def computeHighlightFromRef(self,nodemap):

        x = self.x
        y = self.y
        elemCenters = self.elemCenters
        normals = self.normals

        xHLRef = self.highlightRef[0]
        yHLRef = self.highlightRef[self.verticalID]

        sHL = 0.0
        ptHL = np.array([xHLRef,yHLRef, 0.0])
        nearestNode = -1
        minSqrDist = 1.0e12
        # Find nearest node, but avoiding extremums, since supposed to be at opposite side from HL anyway
        for iNode in range(1,self.nElements):
            nodeIndex = self.ordered[iNode]

            dx = xHLRef - x[nodeIndex]
            dy = yHLRef - y[nodeIndex]
            distSqr =  dx*dx + dy*dy

            if distSqr < minSqrDist:
                minSqrDist = distSqr
                nearestNode = iNode

        nearestNodeDist = sqrt(minSqrDist)
        nearestNodeIndex = self.ordered[nearestNode]
        p = np.array([x[nearestNodeIndex],y[nearestNodeIndex]])

        # Initial guess at nearest node from highlight reference
        ptHL[0] = p[0]
        ptHL[1] = p[1]
        sHL = self.S[nearestNode]

        if minSqrDist > 1.0e-30:
            # Projecting on a circle made by 3 points: The nearest point and its surrondings nodes
            nodeIndex0 = self.ordered[nearestNode-1]
            nodeIndex1 = self.ordered[nearestNode+1]
            p0 = np.array([x[nodeIndex0],y[nodeIndex0]])
            p1 = np.array([x[nodeIndex1],y[nodeIndex1]])

            tx = p1[0] - p0[0]
            ty = p1[1] - p0[1]
            elemArea = sqrt(tx*tx+ty*ty)
            elemCenter = np.array([0.5*(p0[0]+p1[0]),0.5*(p0[1]+p1[1])])
            elemNormal = np.array([-ty/elemArea,tx/elemArea])

            dx = xHLRef - elemCenter[0]
            dy = yHLRef - elemCenter[1]
            projDist = elemNormal[0] * dx + elemNormal[1] * dy
            if projDist > 0.0:
                (cx, cy, r) = define_circle(p,p0,p1)

                for iNodeT in (nearestNode-1, nearestNode+1):
                    nodeIndexT = self.ordered[iNodeT]
                    pt = np.array([x[nodeIndexT],y[nodeIndexT]])

                    found,pointIntersect = line_intersect(xHLRef,yHLRef,cx,cy,p[0],p[1],pt[0],pt[1])

                    if found:
                        dist0ToProj = sqrt(np.sum((pointIntersect-p)**2))
                        area = sqrt(np.sum((pt-p)**2))

                        r1 = dist0ToProj / elemArea

                        if (r1 >= 0.0) & (r1 <= 1.0):
                            sHL = (1.0-r1)*self.S[nearestNode] + r1*self.S[iNodeT]
                            ptHL[0] = pointIntersect[0]
                            ptHL[1] = pointIntersect[1]
                            break

        return (ptHL, sHL)

    ############################
    def computeMetrics(self, nodemap):

        # Computing surface element normals and centers
        self.elemCenters = np.zeros((self.nElements,2), dtype=float)
        self.normals = np.zeros((self.nElements,2), dtype=float)
        self.areas = np.zeros(self.nElements, dtype=float)

        x = self.x;
        y = self.y;

        # Computing surface element normals and centers
        for iElement in range(self.nElements):
            nodeIndex0 = self.ordered[iElement]
            nodeIndex1 = self.ordered[iElement+1]
            self.elemCenters[iElement, 0] = 0.5 * (x[nodeIndex0] + x[nodeIndex1])
            self.elemCenters[iElement, 1] = 0.5 * (y[nodeIndex0] + y[nodeIndex1])

            dx = x[nodeIndex1] - x[nodeIndex0]
            dy = y[nodeIndex1] - y[nodeIndex0]
            area = sqrt(dx*dx+dy*dy)

            self.areas[iElement] = area
            self.normals[iElement, 0] = -dy / (area + 1.0e-8)
            self.normals[iElement, 1] = dx / (area + 1.0e-8)

    ############################
    def setElementConnectivity(self,nodemap):

        x = self.x;
        y = self.y;
        z = self.z;

        # Set reverse node-2-elem connectivity
        # nodeSet = set()
        # for elementI in range(nElements):
        #     for nodeI in range(2):
        #         nodeSet.add(nodemap[elementI,nodeI])
        #
        # nNodes = len(nodeSet)
        #
        # self.node2ElemConnectivity = np.zeros((nNodes,2), dtype=int)
        # countForNode = np.zeros(nNodes, dtype=int)
        #
        # for elementIndex in range(nElements):
        #     for nodeI in range(2):
        #         nodeIndex = nodemap[elementI,nodeI]
        #         self.node2ElemConnectivity[nodeIndex][countForNode[nodeIndex]] = elementIndex
        #         countForNode[nodeIndex] += 1



        # Set elem-2-elem connectivity
        self.elementConnectivity = np.zeros((self.nElements,2), dtype=int)
        # Merging connecting node
        for elementI in range(self.nElements):
            for nodeI in range(2):
                nodeIndex = nodemap[elementI,nodeI]
                xNode = x[nodeIndex]
                yNode = y[nodeIndex]
                for elementJ in range(self.nElements):
                    for nodeJ in range(2):
                        nodeIndex2 = nodemap[elementJ,nodeJ]
                        deltaX = x[nodeIndex2] - xNode
                        deltaY = y[nodeIndex2] - yNode
                        diff = sqrt(deltaX*deltaX+deltaY*deltaY)
                        if (diff < 1e-10):
                            if (nodeIndex2 < nodeIndex):
                                nodemap[elementI,nodeI] = nodeIndex2
                            elif (nodeIndex2 < nodeIndex):
                                nodemap[elementJ,nodeJ] = nodeIndex
                            else:
                                continue

        for i in range(0,self.nElements):
            i0 = nodemap[i][0]
            i1 = nodemap[i][1]

            foundL0 = np.where(nodemap[:,0] == i0)[0]
            foundR0 = np.where(nodemap[:,1] == i0)[0]

            foundL1 = np.where(nodemap[:,0] == i1)[0]
            foundR1 = np.where(nodemap[:,1] == i1)[0]

            if (len(foundL0) > 0):
                for index in foundL0:
                    if (index != i):
                        self.elementConnectivity[i,0] = index
            if (len(foundR0) > 0):
                for index in foundR0:
                    if (index != i):
                        self.elementConnectivity[i,0] = index

            if (len(foundL1) > 0):
                for index in foundL1:
                    if (index != i):
                        self.elementConnectivity[i,1] = index
            if (len(foundR1) > 0):
                for index in foundR1:
                    if (index != i):
                        self.elementConnectivity[i,1] = index

        # Finding trailing edge point
        self.ptTE,self.nodeTEId,self.elemTEId,self.TEposInElem = self.findTrailingEdge(nodemap)

        self.startIndex = self.elemTEId
        nextNodeIndex = nodemap[self.elemTEId, 1-self.TEposInElem]

        index = self.startIndex
        indexPrev = self.elemTEId
        indexNext = None

        if (nextNodeIndex in nodemap[self.elementConnectivity[index,0]][:]):
            indexNext = self.elementConnectivity[index,0]
        else:
            indexNext = self.elementConnectivity[index,1]

        # Build ordered elem-2-node connectivity and node list
        self.node2OrderedNode = np.zeros(self.nNodes+1,dtype=int)
        self.ordered = np.zeros(self.nElements+1,dtype=int)
        self.S = np.zeros(self.nElements+1)

        for i in range(0,self.nElements):
            if (nodemap[indexNext][0] == nodemap[index][0]):
                i0 = nodemap[index][1]
                i1 = nodemap[index][0]
            elif (nodemap[indexNext][0] == nodemap[index][1]):
                i0 = nodemap[index][0]
                i1 = nodemap[index][1]
            elif (nodemap[indexNext][1] == nodemap[index][0]):
                i0 = nodemap[index][1]
                i1 = nodemap[index][0]
            elif (nodemap[indexNext][1] == nodemap[index][1]):
                i0 = nodemap[index][0]
                i1 = nodemap[index][1]
            else:
                print(nodemap[indexNext][0],nodemap[indexNext][1])
                ErrorQuit("Element connectivity is not working!")

            if (i == 0):
                self.ordered[i] = i0

            self.ordered[i+1] = i1;

            indexPrev = index
            index = indexNext
            if (self.elementConnectivity[index,0] == indexPrev):
                indexNext = self.elementConnectivity[index,1]
            else:
                indexNext = self.elementConnectivity[index,0]

        for i in range(0,self.nElements+1):
            self.node2OrderedNode[self.ordered[i]] = i

        # Computing ordered curvilinear distance
        self.S[0] = 0.0

        for nodeI in range(1,self.nElements+1):
            nodeIndex = self.ordered[nodeI]
            nodeIndexPrev = self.ordered[nodeI-1]
            self.S[nodeI] = self.S[nodeI-1] + sqrt((x[nodeIndex]-x[nodeIndexPrev])**2 + (y[nodeIndex]-y[nodeIndexPrev])**2)

        # Computing metrics
        self.computeMetrics(nodemap)

        # Finding highlight location to obtain wrap distance
        if (self.highlightRef[0] > -1.0e5) & (self.highlightRef[1] > -1.0e5) & (self.highlightRef[2] > -1.0e5):
            self.ptHighlight,self.sHighlight = self.computeHighlightFromRef(nodemap)
            print("Highlight from ref = ", self.ptHighlight[0], " ", self.ptHighlight[1], " ",self.ptHighlight[2], " with ref at ", self.highlightRef[0], " ", self.highlightRef[self.verticalID], " ",self.highlightRef[self.spanID], " in axial, vertical and span reference")
        else:
            self.ptHighlight,self.sHighlight = self.computeHighlightFromTE(nodemap, self.ptTE)
            print("Highlight from TE = ", self.ptHighlight[0], " ", self.ptHighlight[1], " ",self.ptHighlight[2], " in axial, vertical and span reference")


        # Computing wrap distance
        for nodeI in range(self.nElements+1):
            self.S[nodeI] -= self.sHighlight


    ############################
    def computeIceThickness(self,nodemap):
        nodemap = self.getNodeMap()
        useExactSurface = False
        circleMethod = True

        xIce = self.xIce;
        yIce = self.yIce;

        if self.cleanSlice != None:
            elemCentersClean = self.cleanSlice.elemCenters
            normalsClean = self.cleanSlice.normals
            areasClean = self.cleanSlice.areas
            xClean = self.cleanSlice.x;
            yClean = self.cleanSlice.y;
            nElementsClean = self.cleanSlice.nElements
            orderedClean = self.cleanSlice.ordered
            sClean = self.cleanSlice.S
        else:
            elemCentersClean = self.elemCenters
            normalsClean = self.normals
            areasClean = self.areas
            xClean = self.x;
            yClean = self.y;
            nElementsClean = self.nElements
            orderedClean = self.ordered
            sClean = self.S

        for iNode in range(self.nElements+1):
            nodeIndexIce = self.ordered[iNode]
            localXIce = xIce[nodeIndexIce]
            localYIce = yIce[nodeIndexIce]
            firstNodeTested = 0
            if iNode > 1:
                firstNodeTested = 1

            nearestNode = -1
            minSqrDist = 1.0e12
            foundElement = False
            elemProj=-1
            for iNodeClean in range(firstNodeTested,nElementsClean+1):
                nodeIndex0 = orderedClean[iNodeClean]

                dx = localXIce - xClean[nodeIndex0]
                dy = localYIce - yClean[nodeIndex0]
                distSqr =  dx*dx + dy*dy

                if distSqr < minSqrDist:
                    minSqrDist = distSqr
                    nearestNode = iNodeClean

            nearestNodeDist = sqrt(minSqrDist)
            nearestNodeIndex = orderedClean[nearestNode]
            pClean = np.array([xClean[nearestNodeIndex],yClean[nearestNodeIndex]])
            self.sThickness[iNode] = sClean[nearestNode]
            self.hIce[iNode] = sqrt((localXIce-pClean[0])*(localXIce-pClean[0])+(localYIce-pClean[1])*(localYIce-pClean[1]))

            if minSqrDist > 1.0e-30:
                # Projecting on real surface line elements
                if (nearestNode == 0) | (nearestNode == nElementsClean) | useExactSurface:
                    iElement0 = nearestNode - 1
                    iElement1 = nearestNode
                    if nearestNode == 0:
                        iElement0 = nElementsClean-1
                        iElement1 = nearestNode
                    elif nearestNode == nElementsClean:
                        iElement0 = nearestNode - 1
                        iElement1 = 0

                    minDist = sqrt(minSqrDist)
                    for iElement in (iElement0, iElement1):
                        nodeIndex0 = orderedClean[iElement]
                        nodeIndex1 = orderedClean[iElement+1]
                        p0 = np.array([xClean[nodeIndex0],yClean[nodeIndex0]])
                        p1 = np.array([xClean[nodeIndex1],yClean[nodeIndex1]])

                        dx = localXIce - elemCentersClean[iElement,0]
                        dy = localYIce - elemCentersClean[iElement,1]
                        elemNormal = normalsClean[iElement]
                        elemArea = areasClean[iElement]
                        projDist = elemNormal[0] * dx + elemNormal[1] * dy
                        if projDist > 0.0:
                            xProj = localXIce - projDist*elemNormal[0]
                            yProj = localYIce - projDist*elemNormal[1]

                            tVecL = np.array([xProj-p0[0],yProj-p0[1]])
                            tVecR = np.array([p1[0]-xProj,p1[1]-yProj])

                            dotProd = np.sum(tVecL*tVecR)
                            if dotProd > 0.0:
                                dist0ToProj = sqrt(np.sum(tVecL**2))

                                r1 = dist0ToProj / elemArea

                                if (r1 >= 0.0) & (r1 <= 1.0):
                                    elemProj = iElement
                                    ptProj = np.array([xProj,yProj])
                                    sProj = r1*sClean[iElement] + (1.0 - r1)*sClean[iElement+1]
                                    localHIce = sqrt((localXIce-ptProj[0])*(localXIce-ptProj[0])+(localYIce-ptProj[1])*(localYIce-ptProj[1]))
                                    self.sThickness[iNode] = sProj
                                    self.hIce[iNode] = projDist
                                    foundElement = True
                                    #break

                else:
                    nodeIndex0 = orderedClean[nearestNode-1]
                    nodeIndex1 = orderedClean[nearestNode+1]
                    p0 = np.array([xClean[nodeIndex0],yClean[nodeIndex0]])
                    p1 = np.array([xClean[nodeIndex1],yClean[nodeIndex1]])

                    tx = p1[0] - p0[0]
                    ty = p1[1] - p0[1]
                    elemArea = sqrt(tx*tx+ty*ty)
                    elemCenter = np.array([0.5*(p0[0]+p1[0]),0.5*(p0[1]+p1[1])])
                    elemNormal = np.array([-ty/elemArea,tx/elemArea])

                    dx = localXIce - elemCenter[0]
                    dy = localYIce - elemCenter[1]
                    projDist = elemNormal[0] * dx + elemNormal[1] * dy
                    if projDist > 0.0:
                        if circleMethod:
                            (cx, cy, r) = define_circle(pClean,p0,p1)

                            for iNodeT in (nearestNode-1, nearestNode+1):
                                nodeIndexT = orderedClean[iNodeT]
                                pt = np.array([xClean[nodeIndexT],yClean[nodeIndexT]])

                                found,pointIntersect = line_intersect(localXIce,localYIce,cx,cy,pClean[0],pClean[1],pt[0],pt[1])

                                if found:
                                    dist0ToProj = sqrt(np.sum((pointIntersect-pClean)**2))
                                    area = sqrt(np.sum((pt-pClean)**2))

                                    r1 = dist0ToProj / elemArea

                                    if (r1 >= 0.0) & (r1 <= 1.0):
                                        sProj = (1.0-r1)*sClean[nearestNode] + r1*sClean[iNodeT]
                                        localHIce = sqrt((localXIce-pointIntersect[0])*(localXIce-pointIntersect[0])+(localYIce-pointIntersect[1])*(localYIce-pointIntersect[1]))
                                        self.sThickness[iNode] = sProj
                                        self.hIce[iNode] = projDist
                                        foundElement = True

                        else:
                            xProj = localXIce - projDist*elemNormal[0]
                            yProj = localYIce - projDist*elemNormal[1]

                            tVecL = np.array([xProj-p0[0],yProj-p0[1]])
                            tVecR = np.array([p1[0]-xProj,p1[1]-yProj])

                            dotProd = np.sum(tVecL*tVecR)
                            if dotProd > 0.0 :
                                dist0ToProj = sqrt(np.sum(tVecL**2))

                                r1 = dist0ToProj / elemArea

                                if (r1 >= 0.0) & (r1 <= 1.0):
                                    projCorrection = (pClean[0]-elemCenter[0])*elemNormal[0] + (pClean[1]-elemCenter[1])*elemNormal[1]
                                    ptProj = np.array([xProj,yProj])
                                    sProj = (1.0-r1)*sClean[nearestNode-1] + r1*sClean[nearestNode+1]
                                    localHIce = sqrt((localXIce-ptProj[0])*(localXIce-ptProj[0])+(localYIce-ptProj[1])*(localYIce-ptProj[1]))
                                    self.sThickness[iNode] = sProj
                                    self.hIce[iNode] = projDist-projCorrection
                                    foundElement = True

        # Extracting ice horns height and angle
        lowerHornHeight = 0.0
        upperHornHeight = 0.0
        lowerHornAngle = 0.0
        upperHornAngle = 0.0
        nodeLowerHorn = -1
        nodeUpperHorn = -1
        for iNode in range(self.nElements+1):
            if self.sThickness[iNode] < 0.0:
                if self.hIce[iNode] > lowerHornHeight:
                    lowerHornHeight = self.hIce[iNode]
                    nodeLowerHorn = iNode
            if self.sThickness[iNode] >= 0.0:
                if self.hIce[iNode] > upperHornHeight:
                    upperHornHeight = self.hIce[iNode]
                    nodeUpperHorn = iNode

        if nodeLowerHorn > -1:
            nodeIndexLowerHorn = self.ordered[nodeLowerHorn]
            localXIce = xIce[nodeIndexLowerHorn]
            localYIce = yIce[nodeIndexLowerHorn]
            dx = localXIce - self.ptHighlight[0]
            dy = localYIce - self.ptHighlight[1]
            lowerHornAngle = atan2(dy, dx) * 180.0 / pi+360.0

        if nodeUpperHorn > -1:
            nodeIndexUpperHorn = self.ordered[nodeUpperHorn]
            localXIce = xIce[nodeIndexUpperHorn]
            localYIce = yIce[nodeIndexUpperHorn]
            dx = localXIce - self.ptHighlight[0]
            dy = localYIce - self.ptHighlight[1]
            upperHornAngle = atan2(dy, dx) * 180.0 / pi

        self.upperHornHeight = upperHornHeight
        self.upperHornAngle = upperHornAngle
        self.lowerHornHeight = lowerHornHeight
        self.lowerHornAngle = lowerHornAngle

    ############################
    def getVariable(self,variable):
        return self.zone.values(variable).as_numpy_array()

    ############################
    def getNumberOfVariables(self):
        return self.zone.num_variables

    ############################
    def getName(self):
        return self.zone.name

    ############################
    def getIndex(self):
        return self.zone.index

    ############################
    def getNumElements(self):
        if (self.initialDataRank==1) & (self.isCGNS):
            return self.zone.num_elements//2
        else:
            return self.zone.num_elements

    ############################
    def getNumNodes(self):
        if self.isOrdered:
            return self.zone.dimensions[0]*self.zone.dimensions[1]*self.zone.dimensions[2]
        else:
            return self.zone.num_nodes

    ############################
    def getNodeMap(self):
        if (self.zone.rank==1) & (self.zone.zone_type == tecplot.constant.ZoneType.Ordered):
            numElements = self.getNumElements()
            numNodes = self.getNumNodes()
            nodemap = np.zeros((numElements,2),dtype=int)
            for i in range(numElements):
                nodemap[i,0] = i
                nodemap[i,1] = i+1

            # Checking if cut is closed
            x = self.getVariable(self.xVar)
            y = self.getVariable(self.yVar)
            dx = x[0] - x[numNodes-1]
            dy = y[0] - y[numNodes-1]
            if sqrt(dx*dx + dy*dy) < 1.0e-10:
                nodemap[numElements-1,1] = 0

            return nodemap
        else:
            return np.array(self.zone.nodemap[:self.getNumElements()][:])

    ############################
    def write(self, outputfile,variables=None,pointFormat=False):
        zones = [self.getIndex()]

        if outputfile.endswith('.plt'):
            tecplot.data.save_tecplot_plt(outputfile,dataset=self.dataset,
                                                      use_point_format=pointFormat,
                                                      zones=zones,
                                                      variables=variables)
        elif outputfile.endswith('.dat'):
            tecplot.data.save_tecplot_ascii(outputfile,dataset=self.dataset,
                                                      use_point_format=pointFormat,
                                                      zones=zones,
                                                      variables=variables)
        else:
            ErrorQuit('Unknown file format (e.g. .dat .plt) : ' + outputfile)

    ############################
    def write(self,fid):
        nNodes = len(self.x)
        fid.write("ZONE T=\"Slice-%lf\"" % (self.position[self.spanID]))

        if self.iceCoordExists:
            fid.write("\nAUXDATA HIGHLIGHT_X  = \"%.12lf\"" % self.ptHighlight[0])
            fid.write("\nAUXDATA HIGHLIGHT_Y  = \"%.12lf\"" % self.ptHighlight[self.verticalID])
            fid.write("\nAUXDATA HIGHLIGHT_Z  = \"%.12lf\"" % self.ptHighlight[self.spanID])
            fid.write("\nAUXDATA LOWER_HORN_HEIGHT  = \"%.12lf\"" % self.lowerHornHeight)
            fid.write("\nAUXDATA LOWER_HORN_ANGLE  = \"%.12lf\"" % self.lowerHornAngle)
            fid.write("\nAUXDATA UPPER_HORN_HEIGHT  = \"%.12lf\"" % self.upperHornHeight)
            fid.write("\nAUXDATA UPPER_HORN_ANGLE  = \"%.12lf\"" % self.upperHornAngle)
            fid.write("\nAUXDATA INTEGRATED_ICE_MASS  = \"%.12lf\"" % self.iceMass)

        for i in range(0,self.nElements+1):
            i0 = self.ordered[i]
            fid.write("\n")
            for v in range(self.getNumberOfVariables()):
                fid.write("%.12lf " % (self.getVariable(v)[i0]))
            fid.write("%.12lf %.12lf %.12lf " % (self.S[i],self.x[i0],self.y[i0]))
            if self.iceCoordExists:
                fid.write("%.12lf %.12lf %.12lf %.12lf " % (self.xIce[i0],self.yIce[i0],self.sThickness[i],self.hIce[i]))

        fid.write("\n")

    ############################
    def writeIPW3Format(self,fid,variableNameAliases,axis,binID,outputType,roughnessKS,writeAuxData=True):
        nNodes = len(self.x)
        zoneName = "SLICE_%s_%s_BINS%s" % (axis.upper(), self.ipw3SlicePositionName, binID)
        if roughnessKS != None:
            zoneName += "_KS_%smm" % formatIPW3NameValue(roughnessKS)
        zoneName += "_%s" % outputType
        fid.write("ZONE T=\"%s\"" % zoneName)

        if writeAuxData and self.iceCoordExists:
            fid.write("\nAUXDATA HIGHLIGHT_X  = \"%.5lf\"" % self.ptHighlight[0])
            fid.write("\nAUXDATA HIGHLIGHT_Y  = \"%.5lf\"" % self.ptHighlight[self.verticalID])
            fid.write("\nAUXDATA HIGHLIGHT_Z  = \"%.5lf\"" % self.ptHighlight[self.spanID])
            fid.write("\nAUXDATA LOWER_HORN_HEIGHT  = \"%.5lf\"" % self.lowerHornHeight)
            fid.write("\nAUXDATA LOWER_HORN_ANGLE  = \"%.5lf\"" % self.lowerHornAngle)
            fid.write("\nAUXDATA UPPER_HORN_HEIGHT  = \"%.5lf\"" % self.upperHornHeight)
            fid.write("\nAUXDATA UPPER_HORN_ANGLE  = \"%.5lf\"" % self.upperHornAngle)
            fid.write("\nAUXDATA INTEGRATED_ICE_MASS  = \"%.5lf\"" % self.iceMass)

        def normalizeVariableName(name):
            return name.lower().replace("_", "").replace(" ", "")

        def findVariableID(aliases, sourceSlice):
            aliasKeys = [normalizeVariableName(name) for name in aliases]
            for v in range(sourceSlice.getNumberOfVariables()):
                variableName = sourceSlice.tecplotdataset.getVariableName(variable=v)
                if normalizeVariableName(variableName) in aliasKeys:
                    return v
            return -1

        varIDs = [findVariableID(aliases, self) for aliases in variableNameAliases]
        cleanSolutionSlice = getattr(self, "cleanSolutionSlice", None)
        htcCleanID = -1
        if cleanSolutionSlice != None:
            htcCleanID = findVariableID(variableNameAliases[-1], cleanSolutionSlice)

        for i in range(0,self.nElements+1):
            i0 = self.ordered[i]
            fid.write("\n")
            for iVar in range(len(variableNameAliases)):
                if variableNameAliases[iVar][0] == "HTC_CLEAN" and htcCleanID > -1 and i < len(cleanSolutionSlice.ordered):
                    iClean = cleanSolutionSlice.ordered[i]
                    fid.write("%.5lf " % (cleanSolutionSlice.getVariable(htcCleanID)[iClean]))
                elif varIDs[iVar] > -1:
                    fid.write("%.5lf " % (self.getVariable(varIDs[iVar])[i0]))
                else:
                    fid.write("%.5lf " % (-999.0))


        fid.write("\n\n")

############################
class TecplotDataSet(object):
    """docstring for TecplotDataSet"""

    ############################
    def __init__(self):
        self.dataset = None
        self.frame = tecplot.active_page().add_frame()

    ############################
    def loadData(self,tecplotFiles,zoneName=None):
        self.isCGNS = False
        for tecplotFile in tecplotFiles:
            if tecplotFile.endswith('.cgns'):
                self.isCGNS = True

        if self.isCGNS:
            self.dataset = tecplot.data.load_cgns(tecplotFiles, frame=self.frame);
        else:
            self.dataset = tecplot.data.load_tecplot(tecplotFiles, frame=self.frame);

        if zoneName != None:
            if zoneName not in self.dataset.zone_names:
                ErrorQuit("Zone '%s' not found. Available zones: %s" % (zoneName, ", ".join(self.dataset.zone_names)))
            zonesToDelete = [zone for zone in self.dataset.zones() if zone.name != zoneName]
            if len(zonesToDelete) > 0:
                self.dataset.delete_zones(*zonesToDelete)

    ############################
    def newDataSet(self, name):
        if (self.dataset == None):
            ErrorQuit("Dataset already exists")

        self.dataset = tecplot.active_frame().create_dataset(name)

    ############################
    def getVariable(self,zone=0,variable='x'):
        return self.dataset.zone(zone).values(variable).as_numpy_array()

    ############################
    def getVariableName(self,zone=0,variable='x'):
        return self.dataset.variable(variable).name

    ############################
    def getNumberOfZones(self):
        return self.dataset.num_zones

    ############################
    def getNumberOfVariables(self):
        return self.dataset.num_variables

    ############################
    def getZone(self,zone):
        return self.dataset.zone(zone)

    ############################
    def slice(self,pos,normal,chord,axis,rotationAngle, highlight, requestOrdering, cleanSlice):
        frame = self.frame
        frame.plot_type = tecplot.constant.PlotType.Cartesian3D

        initialDataRank =  self.dataset.zone(0).rank

        # If data is already a slice, directly uses the loaded zone
        if initialDataRank == 1:
            return Slice(self.dataset.zone(0), self, normal, pos,chord,axis, rotationAngle, highlight, requestOrdering, initialDataRank, cleanSlice)
        else:
            extracted_slice = tecplot.data.extract.extract_slice(
                                    origin=(pos[0], pos[1], pos[2]),
                                    normal=(normal[0], normal[1], normal[2]),
                                    source=tecplot.constant.SliceSource.SurfaceZones,
                                    dataset=self.dataset,
                                    mode=tecplot.constant.ExtractMode.SingleZone,
                                    frame=frame)
            return Slice(extracted_slice, self, normal, pos,chord,axis, rotationAngle, highlight, requestOrdering, initialDataRank, cleanSlice)


    ############################
    def write(self, outputfile,zones=None,variables=None,pointFormat=False):

        if outputfile.endswith('.plt'):
            tecplot.data.save_tecplot_plt(outputfile,dataset=self.dataset,
                                                      use_point_format=pointFormat,
                                                      zones=zones,
                                                      variables=variables)
        elif outputfile.endswith('.dat'):
            tecplot.data.save_tecplot_ascii(outputfile,dataset=self.dataset,
                                                      use_point_format=pointFormat,
                                                      zones=zones,
                                                      variables=variables)
        else:
            ErrorQuit('Unknown file format (e.g. .dat .plt) : ' + outputfile)

############################
def formatIPW3NameValue(value):
    try:
        value = "%.12g" % float(value)
    except ValueError:
        value = str(value)
    return value.replace("-", "m").replace(".", "p")

def formatIPW3SlicePosition(position):
    return formatIPW3NameValue(position)

############################
def performSlices(args):
    dataset = TecplotDataSet()
    dataset.loadData(args.tecplotFiles,args.zoneName)

    cleanDataset = None
    if args.cleanGrid != None:
        cleanDataset = TecplotDataSet()
        cleanDataset.loadData(args.cleanGrid)

    cleanSolutionDataset = None
    if args.cleanSolution != None:
        cleanSolutionDataset = TecplotDataSet()
        cleanSolutionDataset.loadData(args.cleanSolution)

    slices = []
    slicesIndex = []
    pos = [0.0,0.0,0.0]
    axisNormal = [0.0,0.0,0.0]

    if (args.axis == 'x'):
        axisIndex = 0
        otherIndex = [1,2]
        axisNormal = [1.0,0.0,0.0]
    elif (args.axis == 'y'):
        axisIndex = 1
        otherIndex = [0,2]
        axisNormal = [0.0,1.0,0.0]
    elif (args.axis == 'z'):
        axisIndex = 2
        otherIndex = [0,1]
        axisNormal = [0.0,0.0,1.0]
    else:
        ErrorQuit("Unknown axis: " + args.axis)

    if (len(args.normal) != 3):
        ErrorQuit("Normal vector must be length 3!")

    var = None
    otherVar1 = None
    otherVar2 = None
    if cleanDataset != None:
        var = cleanDataset.getVariable(variable=axisIndex)
        otherVar1 = cleanDataset.getVariable(variable=otherIndex[0])
        otherVar2 = cleanDataset.getVariable(variable=otherIndex[1])
    else:
        var = dataset.getVariable(variable=axisIndex)
        otherVar1 = dataset.getVariable(variable=otherIndex[0])
        otherVar2 = dataset.getVariable(variable=otherIndex[1])

    if (args.pos == None):
        ds = abs(var.min() - var.max())
        ds *= 0.001
        args.pos = np.linspace(var.min()+ds, var.max()-ds, args.nslice)

    nSlice = len(args.pos)

    # Looping over the number of slices to produce
    for i in range(0,nSlice):
        requestedSlicePosition = args.pos[i]
        pos[axisIndex] = requestedSlicePosition
        pos[otherIndex[0]] = 0.0
        pos[otherIndex[1]] = 0.0

        tmpDataSet=dataset
        if cleanDataset != None:
            tmpDataSet = cleanDataset

        tmpSlice = tmpDataSet.slice(pos,axisNormal,args.chord, args.axis, args.angle, args.highlight, False, None)

        idNodeMinX = tmpSlice.x.argmin()

        pos[axisIndex] = tmpSlice.z[idNodeMinX]
        pos[otherIndex[0]] = tmpSlice.x[idNodeMinX]
        pos[otherIndex[1]] = tmpSlice.y[idNodeMinX]

        # try:
        cleanSlice = None
        if cleanDataset != None:
            print("Preparing clean data")
            cleanSlice = cleanDataset.slice(pos,args.normal,args.chord, args.axis, args.angle, args.highlight, True, None)

        cleanSolutionSlice = None
        if cleanSolutionDataset != None:
            print("Preparing clean solution data")
            cleanSolutionSlice = cleanSolutionDataset.slice(pos,args.normal,args.chord, args.axis, args.angle, args.highlight, True, None)

        print("Preparing data")
        slices.append(dataset.slice(pos,args.normal,args.chord, args.axis, args.angle, args.highlight, True, cleanSlice))
        slices[-1].cleanSolutionSlice = cleanSolutionSlice
        slices[-1].ipw3SlicePositionName = formatIPW3SlicePosition(requestedSlicePosition)
        slicesIndex.append(slices[-1].getIndex())
        # except:
            # continue

    # Prepparing header of output file
    iceCoordExists = False
    for s in slices:
        if s.iceCoordExists:
            iceCoordExists = True

    ipw3VariableNameAliases = args.ipw3VariableNameAliases

    fid = open(args.output,"w")
    if args.ipw3:
        fid.write("VARIABLES =")
        for aliases in ipw3VariableNameAliases:
            fid.write(" \"%s\"" % (aliases[0]))
        fid.write("\n")
    else:
        fid.write("VARIABLES= ")
        for v in range(dataset.getNumberOfVariables()):
            fid.write(" \"%s\"" % (dataset.getVariableName(variable=v)))
        fid.write(" \"s\" \"x2d\" \"y2d\"")

        if iceCoordExists:
            fid.write(" \"x2d_ice\" \"y2d_ice\" \"sClean\" \"hIce\"\n")
        else:
            fid.write("\n")

    # Writing data from each slice into output file
    for s in slices:
        # Translate cut to position highlight as origin
        # print("Position slice at origin")
        for nodeIndex in range(s.nNodes):
            s.x[nodeIndex] -= s.ptHighlight[0]
            s.y[nodeIndex] -= s.ptHighlight[1]
            if s.iceCoordExists:
                s.xIce[nodeIndex] -= s.ptHighlight[0]
                s.yIce[nodeIndex] -= s.ptHighlight[1]

        # Scaling the coordinates
        scale = float(args.scale)
        for nodeIndex in range(s.nNodes):
            s.x[nodeIndex] *= scale
            s.y[nodeIndex] *= scale
            if s.iceCoordExists:
                s.xIce[nodeIndex] *= scale
                s.yIce[nodeIndex] *= scale

        for iNode in range(s.nElements+1):
            s.S[iNode] *= scale
            if s.iceCoordExists:
                s.sThickness[iNode] *= scale
                s.hIce[iNode] *= scale

        if s.iceCoordExists:
            s.ptHighlight[0] *= scale
            s.ptHighlight[1] *= scale
            s.ptHighlight[2] *= scale
            s.upperHornHeight *= scale
            s.lowerHornHeight *= scale

        if args.ipw3:
            s.writeIPW3Format(fid, ipw3VariableNameAliases, args.axis, args.binID, args.OutputType, args.roughnessKS, not args.ipw3_ICE_SHAPE)
        else:
            s.write(fid)
    fid.close()
    print("Saved output file: %s" % os.path.abspath(args.output))

    return slices

############################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Tecplot API', prog = 'TecPy')
    parser.add_argument('-axis', help = 'Axis direction to perform the slice(s) (x, y, z)')
    parser.add_argument('-pos', help = 'Position along the axis to perform the slice(s)', nargs='+', type=float)
    parser.add_argument('-normal', help = 'Normal of the plane cut <nx,ny,nz>', nargs='+', type=float)
    parser.add_argument('-nslice', help='Number of slices to be performed using extremums as star and end position', type=int)
    parser.add_argument('-tecplotFiles', help = 'Tecplot data files', nargs = '+')
    parser.add_argument('-zoneName', help = 'Only slice this Tecplot zone name')
    parser.add_argument('-cleanGrid', help = 'Tecplot data file containing clean grid', nargs = '+')
    parser.add_argument('-cleanSolution', help = 'Tecplot data file containing clean solution values for HTC_CLEAN', nargs = '+')
    parser.add_argument('-output', help = 'Output file')
    parser.add_argument('-chord', help = 'Chord for lift adim if you want to force it (don''t define if you want it to be computed automaticly) ', type=float)
    parser.add_argument('-cp', help='Index of variable containing Cp in the tecplot dataset', type=int)
    parser.add_argument('-cfx', help='Index of variable containing Cfx in the tecplot dataset', type=int)
    parser.add_argument('-cfy', help='Index of variable containing Cfy in the tecplot dataset', type=int)
    parser.add_argument('-cfz', help='Index of variable containing Cfz in the tecplot dataset', type=int)
    parser.add_argument('-angle', help='Rotation angle to apply to geometry before computing the ice data', type=float, default=0.0)
    parser.add_argument('-scale', help='Scale to apply to coordinates when writing output', type=float, default=1.0)
    parser.add_argument('-highlight', help='High-light point to project on surface <x,y,z>', nargs='+', type=float)
    parser.add_argument('--ipw3', help='Write output formatted for IPW3 submission', action='store_true')
    parser.add_argument('--ipw3_CUTDATA', help='Write IPW3 cut data output', action='store_true')
    parser.add_argument('--ipw3_ICE_SHAPE', help='Write IPW3 ice shape output', action='store_true')
    parser.add_argument('--binID', help='Bin identifier used in IPW3 zone names after BINS', default='XX')
    parser.add_argument('--OutputType', help='Dataset identifier used in IPW3 zone names, e.g. D01', default='D01')
    parser.add_argument('--roughnessKS', help='Optional roughness ks value in mm inserted into IPW3 zone names, e.g. 1.0 -> KS_1mm')

    args = parser.parse_args()
    args.ipw3 = args.ipw3 or args.ipw3_CUTDATA or args.ipw3_ICE_SHAPE

    if args.ipw3_ICE_SHAPE:
        args.ipw3VariableNameAliases = [
            ["X", "CoordinateX"],
            ["Y", "CoordinateY"],
            ["Z", "CoordinateZ"],
            ["X_ICED", "X_Iced", "X_iced", "CoordinateX_Iced", "CoordinateX_iced", "x_ice"],
            ["Y_ICED", "Y_Iced", "Y_iced", "CoordinateY_Iced", "CoordinateY_iced", "y_ice"],
            ["Z_ICED", "Z_Iced", "Z_iced", "CoordinateZ_Iced", "CoordinateZ_iced", "z_ice"]
        ]
    else:
        args.ipw3VariableNameAliases = [
            ["X", "CoordinateX"],
            ["Y", "CoordinateY"],
            ["Z", "CoordinateZ"],
            ["Cp", "PressureCoefficient"],
            ["HTC", "HeatTransferCoefficient", "HTC_Roughness", "HTCRoughness"],
            ["Beta", "CollectionEfficiency"],
            ["Ts", "WallTemperature", "SurfaceTemperature"],
            ["FF", "FreezingFraction"],
            ["k", "ks", "RoughnessHeight"],
            ["RhoIce", "IceDensity", "Rho_Ice"],
            ["HTC_CLEAN", "HTCClean", "CleanHTC", "HTC_Clean"]
        ]

    if (args.highlight != None):
        if (len(args.highlight) != 3):
            ErrorQuit("Highlight requires 3 components separated by spaces")
    else:
        args.highlight = np.array([-1e6,-1e6,-1e6])

    if (args.normal != None):
        if (len(args.normal) != 3):
            ErrorQuit("Normal requires 3 components separated by spaces")

    if (args.tecplotFiles == None):
        ErrorQuit('Missing tecplot files!')

    if (args.normal == None):
        ErrorQuit('Missing normal vector for plane cut!')

    if (args.pos == None and args.nslice == None):
        ErrorQuit('Missing position for cuts!')

    if (args.pos != None and args.nslice != None):
        ErrorQuit('Cannot define both position and number of cuts')

    if (args.axis == None):
        ErrorQuit('Missing axis direction for cut position!')

    if (args.output == None):
        ErrorQuit('Missing output file!')

    slices = performSlices(args)

