import csv
import numpy as np
from scipy import integrate
import pandas as pd
import os
from matplotlib import pyplot as plt
import statistics


nonencodedDir = '/Users/luisjessen/Documents/REU/PythonScripts/DSC/DSCAutomation/DSCCSV/'
directory = os.fsencode(nonencodedDir)


def readingCSV(fileName, mode):
    '''
    This function is passed a fileName. This file it then opens, does some slight formatting and reads through it.
    '''
    with open(fileName, 'r') as file:
        csvReader = csv.reader((line.replace('\0', '')
                               for line in file), file, delimiter=',')
        lineCount = 0
        startCollection = False
        timeArrayMinutes = []
        ConvHF = []
        mass = 0

        for line in csvReader:

            # for some reason \t would be squeezed in between each element of the list
            lineList = line[0].split(sep='\t')

            if lineList[0] == 'TEMPERATURE CALIBRATION INPUTS:':
                break

            if lineList[0] == 'Sample Weight:' and mode == 'massSearch':
                mass = lineList[1]
                mass = mass.replace(' mg', '')
                print(float(mass))

            if startCollection:

                if mode == 'timeConv':
                    timeArrayMinutes.append(lineList[0])

                if mode == 'HFConv':
                    ConvHF.append(lineList[1])

            if lineList[0] == '1) DSC Isothermal':
                startCollection = True

        if mode == 'timeConv':
            timeArraySeconds = [
                float(element) * 60 for element in timeArrayMinutes]
            return timeArraySeconds

        if mode == 'HFConv':
            ConvHF = [float(x) for x in ConvHF]
            positiveHF = [-x for x in ConvHF]
            return positiveHF

        if mode == 'massSearch':
            return float(mass)


# Encoding thedirectory using os.listdir and then looping through the folder

i = 0
for file in os.listdir(directory):
    fileName = os.fsdecode(file)
    read_file = pd.read_csv(nonencodedDir + fileName,
                            error_bad_lines=False, sep='[;,]', header=None, engine='python')
    read_file.to_csv(r'80 mW 2 cont.csv', mode='w', index=False)
    print(fileName)

    fileName = '80 mW 2 cont.csv'
    timeArraySeconds = readingCSV(fileName, mode='timeConv')
    positiveHF = readingCSV(fileName, mode='HFConv')
    mass = readingCSV(fileName, mode='massSearch')
    # Making dictionary that relates time and positiveHF

    HFTimeDict = dict(zip(timeArraySeconds, positiveHF))
    plt.figure(1)
    plt.plot(timeArraySeconds, positiveHF, '-r', label='HF v. Time')
    plt.xlim([0, 1200])
    plt.xlabel('Time (s)')
    plt.ylabel('Heatflow (mW)')
    plt.title('Raw Graph')
    plt.show()
    intervalArray = []


def averageInterval(startKey, stopKey):
    '''
    Averages the values in the dictionary between the start and stop key determined in 'determineInterval()'
    '''

    collect = False

    for key in HFTimeDict:
        if key == startKey:
            collect = True
        if key == stopKey:
            break
        if collect:
            intervalArray.append(HFTimeDict[key])
            continue

    intervalAvg = statistics.mean(intervalArray)
    return intervalAvg


def determineInterval():
    '''
    User is asked to determine the interval that will be used to average the final baseline.
    '''

    intBeginningTime = float(input("Start point: "))
    intEndTime = float(input("End point: "))
    #intBeginningTime = 600
    #intEndTime = 700

    '''    
    Take each tuple extracted from HFTimeDict.items, i.e. key-value pairs.
    Apply the function lambda x: abs(value - x[1]) to each tuple, i.e. calculate the absolute difference versus value.
    Calculate the minimum result from the lambda function and return the argument supplied, in this case a single tuple from d.items.
    key=lambda x: is an inline function that finds the absolute value between the input value and every key in the dictionary.
    https://stackoverflow.com/questions/52844099/finding-the-closest-value-in-a-python-dictionary-and-returning-its-key
    '''
    res_keyStart, res_valStart = min(
        HFTimeDict.items(), key=lambda x: abs(intBeginningTime - x[0]))
    intBeginningHF = HFTimeDict[res_keyStart]
    res_keyEnd, res_valEnd = min(
        HFTimeDict.items(), key=lambda x: abs(intEndTime - x[0]))
    intEndHF = HFTimeDict[res_keyEnd]
    print(res_keyStart)
    print(res_keyEnd)
    return averageInterval(res_keyStart, res_keyEnd)


intervalAvg = determineInterval()
yCorrectedHF = [float(x) - intervalAvg for x in positiveHF]
print(intervalAvg)


correctedTimeArray = []


def correctTime():
    '''
    Searches for the first item in the dictionary that corresponds to a positive HF value, takes that time key and then uses it 
    to shift down the entire time array.
    '''

    HFTimeDictCorrected = dict(zip(timeArraySeconds, yCorrectedHF))
    for key in HFTimeDictCorrected:
        # print(HFTimeDictCorrected)
        if HFTimeDictCorrected[key] > 0:
            timeCorrection = key
            break

    correctedTimeArray = [item - timeCorrection for item in timeArraySeconds]

    plt.figure(2)
    plt.plot(correctedTimeArray, yCorrectedHF, 'k-', label='Normalized Graph')
    plt.xlim([0, 800])

    plt.xlabel('Time (s)')
    plt.ylabel('Heatflow (mW)')
    plt.title('Normalized Graph')
    plt.show()
    return HFTimeDictCorrected, correctedTimeArray, timeCorrection


HFTimeDictCorrected, correctedTimeArray, timeCorrection = correctTime()


'''
Create two new lists. One with the shifted time axis and one with the shifted HF axis.
'''

finalTime = []
finalHF = []


def createNewTHFArray():
    for key in HFTimeDictCorrected:

        if HFTimeDictCorrected[key] > 0:
            finalTime.append(key - timeCorrection)
            finalHF.append(HFTimeDictCorrected[key])
            continue


createNewTHFArray()

deltaH = float(input('\u0394H: '))
#deltaH = 114000
numOfMols = float(input('n: '))
#numOfMols = 2
MF = float(input('MW: '))
#MF = 145
denominator = (deltaH*numOfMols*mass)/MF


def convRate():
    '''
    Uses the denominator already calculated (constant) to find an array for the conversion rate.
    '''
    conversionRate = [item/denominator for item in finalHF]
    plt.figure(2)
    plt.plot(finalTime, conversionRate, 'g-')
    plt.xlim([0, 600])

    plt.xlabel('Time (s)')
    plt.ylabel('Conversion Rate')
    plt.title('Conversion Rate v. Time')
    plt.show()
    return conversionRate


conversionRate = convRate()


def conversion():
    conversion = [0]
    i = 0

    while i < len(finalTime) - 1:
        point = ((finalTime[i+1] - finalTime[i]) *
                 (conversionRate[i+1] + conversionRate[i])/2) + conversion[i]
        conversion.append(point)
        i += 1

    plt.figure(3)
    plt.plot(finalTime, conversion, 'b-')
    plt.xlim([0, 600])

    plt.xlabel('Time (s)')
    plt.ylabel('Conversion')
    plt.title('Conversion Time')
    plt.show()


conversion()
