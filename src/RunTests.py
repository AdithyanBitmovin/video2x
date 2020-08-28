import os
import subprocess
import requests
import urllib
import time
import logging
import argparse
import ntpath
from datetime import datetime
import json

OUTPUT_RESULTS = "./output/results"
OUTPUT_SEGMENTS = "./output/segments"
INPUT_SOURCE = "./input/source"

input = os.getenv("INPUT")
testType = os.getenv("TEST_TYPE")


class Encoder(object):
    def __init__(self, encoderString, preset, encoderOptions):
        self.encoderString = encoderString
        self.preset = preset
        self.encoderOptions = encoderOptions


class Rendition(object):
    def __init__(self, scaling_size, crf):
        self.scaling_size = scaling_size
        self.crf = crf


class Decoder(object):
    def __init__(self, decoderString, decoderOptions):
        self.decoderString = decoderString
        self.decoderOptions = decoderOptions


class TestCase(object):
    def __init__(self, decoder, encoders, renditions, scaler):
        self.decoder = decoder
        self.encoders = encoders
        self.renditions = renditions
        self.scaler = scaler


class ProcessMonitorResult(object):
    def __init__(self, cpuTimeInSecs, cpuUsuageInPercent, maxMemInKb, avgMemInKb, realTimeFactor):
        self.cpuTimeInSecs = cpuTimeInSecs
        self.cpuUsuageInPercent = cpuUsuageInPercent
        self.maxMemInKb = maxMemInKb
        self.avgMemInKb = avgMemInKb
        self.realTimeFactor = realTimeFactor


def main(input):
    logging.basicConfig(level=logging.INFO)

    if input == None:
        logging.error(
            "Links not found. Filename is missing. Try: 'docker run -v %LOCAL_DIRECTORY:/output/ -e INPUT=filename "
            "-it %IMAGE bash'. Using default links instead\n")

    logging.info("Creating I/O directories.")
    createIODirectories([INPUT_SOURCE, OUTPUT_RESULTS, OUTPUT_SEGMENTS])

    logging.info("Checking if there any file which need to be downloaded.")
    videos = downloadVideos(input)
    logging.info("All files are downloaded.\n")

    logging.info("Starting the tests.")
    runTests(videos)
    logging.info("Tests have finished.")


def createIODirectories(directories):
    for dir in directories:
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)


def downloadVideos(filename):
    links = [
        "http://adi-innovation-superresolution.commondatastorage.googleapis.com/source/CONAN/chunk_4s_forced/video_00346.mkv"
    ]

    if (filename is not None):
       links = open("./" + filename, "r").read().split("\n")

    videos, doFilesExist, filesToDownload, downloadSize = checkIfVideosExist(links)
    print("Files to download : " + str(filesToDownload))

    if filesToDownload > 0:
        logging.info(str(filesToDownload) + " missing files ( " + str(downloadSize)[
                                                                  0:-6] + "MB ) need to be downloaded. This may take a while.")

        for i in range(len(videos)):
            if not doFilesExist[i]:
                logging.info("Downloading file #" + str(i + 1) + " - \"" + videos[i] + "\" ( " +
                             urllib.request.urlopen(links[i]).info()["Content-Length"][0:-6] + "MB ). Please wait...")
                os.system("wget -O " + INPUT_SOURCE + "/" + videos[i] + " " + links[i] + " > /dev/null 2>&1")
                filesToDownload -= 1
                logging.info("Finished downloading file #" + str(i + 1) + " - \"" +
                             videos[i] + "\". " + str(filesToDownload) + " files left.")

    return videos


def checkIfVideosExist(links):
    videos = []
    doFilesExist = []
    filesToDownload = 0
    downloadSize = 0

    for i in range(len(links)):
        # Get the video name out of the link
        splitLink = links[i].split("/")[-1]
        videos.append(splitLink)
        filePath = "{0}/{1}".format(INPUT_SOURCE, splitLink)
        doFilesExist.append(os.path.isfile(filePath))

        if not doFilesExist[i]:
            downloadSize += int(urllib.request.urlopen(links[i]).info()["Content-Length"])
            filesToDownload += 1

    return videos, doFilesExist, filesToDownload, downloadSize


# Run the tests for all given encoders, passes, bitrates and presets
def runTests(videos):
    print(testType)
    if (testType == "bicubic"):
        logging.info("Evaluating X264 - bicubic scaling")
        testCase = getTestCase_bicubic()
    else :
        logging.info("Evaluating X264 - " + testType + " scaling")
        testCase = getTestCase_superresolution(testType)

    evalTestData(videos, testCase)


def writeOutputToFile(jsonPrettyString, encoder, dateTimeForFileOutput, scaler):

    outputFilePath = "{0}/{1}/{2}_{3}_{4}_{1}.json".format(OUTPUT_RESULTS, scaler, dateTimeForFileOutput,
                                                      encoder.encoderString, encoder.preset)

    resultsFile = open(outputFilePath, "w")
    resultsFile.write(jsonPrettyString)
    resultsFile.close()
    return outputFilePath


def prettifyJsonString(results):
    jsonData = str(results).replace("\'", "\"")
    jsonObject = json.loads(jsonData)
    jsonPrettyString = json.dumps(jsonObject, indent=2)
    return jsonPrettyString


def getTestCase_bicubic():
    # Initialize encoders
    encoders = []
    x264codecOptionsString = r"""{
        "pix_fmt" : "yuv420p",
        "tune" : "animation"
    }"""
    x264codecOptions = json.loads(x264codecOptionsString)
    encoders.append(Encoder("libx264", "default", x264codecOptions))

    # Intialize renditions
    renditions = []
    renditions.append(Rendition(2, 17))
    renditions.append(Rendition(4, 17))

    # Intialize decoder
    decoder = Decoder("h264", {})

    testCase = TestCase(decoder, encoders, renditions, "scale")
    return testCase


def getTestCase_superresolution(driver):
    # Initialize encoders
    encoders = []

    encoders.append(Encoder("libx264", "default", {}))

    # Intialize renditions
    renditions = []
    renditions.append(Rendition(2, 17))
    renditions.append(Rendition(4, 17))

    decoder = Decoder("h264_cuvid", {})

    testCase = TestCase(decoder, encoders, renditions, driver)
    return testCase


def evalTestData(videos, testCase):
    dateTimeForFileOutput = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    for encoder in testCase.encoders:
        results = []
        for video in videos:
            logging.info(
                "Running tests for: |\t " + video +
                " \t|\t Encoder: " + encoder.encoderString + " \t|\t Preset: " + encoder.preset + " \t|"
                + " \t|\t Scaler: " + testCase.scaler + " \t|")

            testCaseCommand = ""
            if testCase.scaler == "scale":
                testCaseCommand = getFfmpegEncodeCommand(video, testCase.decoder, encoder, testCase.renditions,
                                                         testCase.scaler)
                timeOfCommand = getTimeOfCommand(testCaseCommand)

            else:
                timeOfCommand = getVideo2xEncodeCommand(video, testCase.decoder, encoder, testCase.renditions,
                                                              testCase.scaler)

            processMonitorResult = executeTimeCommand(timeOfCommand)
            bitrateList, psnrList, vmafList = extractBdMetrics(encoder, testCase, video)

            results.append(
                {
                    "video": video,
                    "encoder": encoder.encoderString,
                    "preset": encoder.preset,
                    "time": processMonitorResult.cpuTimeInSecs,
                    "cpuUsage": processMonitorResult.cpuUsuageInPercent,
                    "maxMemoryUsage": processMonitorResult.maxMemInKb,
                    "avgMemoryUsage": processMonitorResult.avgMemInKb,
                    "realTimeFactor": processMonitorResult.realTimeFactor,
                    "bitrateOutput": bitrateList,
                    "psnr": psnrList,
                    "vmaf": vmafList,
                    "scaler" : testCase.scaler
                }
            )

        jsonPrettyString = prettifyJsonString(results)
        outputFilePath = writeOutputToFile(jsonPrettyString, encoder, dateTimeForFileOutput, testCase.scaler)
        logging.info("Results written in {0}".format(outputFilePath))


def extractBdMetrics(encoder, testCase, video):
    bitrateOutputList = []
    psnrOutputList = []
    vmafOutputList = []
    for rendition in testCase.renditions:
        outputPath = getOutputFilePath(rendition, video, encoder, testCase.scaler)
        "{0}/{1}".format(OUTPUT_RESULTS, outputPath)

        sourceInputPath = getInputPath(video)
        bitrateOutput, psnr, vmaf = getBitrateOfVideo(sourceInputPath, outputPath)
        bitrateOutput = 0
        psnr = 0
        vmaf = 0
        bitrateOutputList.append(bitrateOutput)
        psnrOutputList.append(psnr)
        vmafOutputList.append(vmaf)

    bitrateCommaSeparated = ", ".join(map(str, bitrateOutputList))
    psnrCommaSeparated = ", ".join(map(str, psnrOutputList))
    vmafCommaSeparated = ", ".join(map(str, vmafOutputList))

    bitrateFormatted = "[ {0} ]".format(bitrateCommaSeparated)
    psnrFormatted = "[ {0} ]".format(psnrCommaSeparated)
    vmafFormatted = "[ {0} ]".format(vmafCommaSeparated)
    return bitrateFormatted, psnrFormatted, vmafFormatted


def getVideo2xEncodeCommand(video, decoder, encoder, renditionList, scaler):
    video2xpath = "./video2x/src/video2x.py"
    inputPath = getInputPath(video)


    video2xCommandList = []

    for rendition in renditionList:
        createIODirectories([OUTPUT_SEGMENTS + "/" + scaler + "_" + str(rendition.scaling_size) + "x/" ])
        createIODirectories([OUTPUT_RESULTS + "/" + scaler + "_" + str(rendition.scaling_size) + "x/" ])

        outputPath = getOutputFilePath(rendition, video, encoder, scaler)
        video2xCommand = "python3.8 {0} -i {1} -o {2} -d {3} -r {4}".format(video2xpath, inputPath, outputPath, scaler,
                                                                            rendition.scaling_size)
        video2xCommandList.append(getTimeOfCommand(video2xCommand))


    video2xCommandJoint = " && ".join(video2xCommandList)
    return video2xCommandJoint


# Returns the command to encode with the given parameters as a string.
# video - filename
# encoder - x264 / x265
# bitrate in Mbit/s
# preset - slow / fast
def getFfmpegEncodeCommand(video, decoder, encoder, renditionList, scaler):
    ffmpegPath = "ffmpeg -hide_banner -loglevel quiet -stats"
    inputPath = getInputPath(video)

    #decodingOption = "{0} -c:v {1}".format(getOptionsFfmpegString(decoder.decoderOptions), decoder.decoderString)
    decodingOption = ""

    outputRenditionsCommand = ""
    for rendition in renditionList:
        createIODirectories([OUTPUT_SEGMENTS + "/" + scaler + "_" + str(rendition.scaling_size) + "x/" ])
        createIODirectories([OUTPUT_RESULTS + "/" + scaler + "_" + str(rendition.scaling_size) + "x/" ])
        outputRenditionsCommand += getRenditionFfmpegSubCommand(encoder, video, rendition, scaler)

    ffmpegCommand = '{0}  -y {1} -i {2} {3}'.format(ffmpegPath, decodingOption, inputPath, outputRenditionsCommand)
    print(ffmpegCommand)
    return ffmpegCommand


def getInputPath(video):
    inputPath = INPUT_SOURCE + "/" + video
    return inputPath


def getRenditionFfmpegSubCommand(encoder, video, rendition, scaler):
    outputPath = getOutputFilePath(rendition, video, encoder, scaler)
    # outputPath = "-f null /dev/null"

    encoderOptions = getOptionsFfmpegString(encoder.encoderOptions)
    outputRenditions = ' -crf {4} {6} -c:v {2} -vf {7}=iw*{0}:ih*{1},setdar=3/2 -sws_flags bicubic -an {5}'.format(rendition.scaling_size,
                                                                                     rendition.scaling_size,
                                                                                     encoder.encoderString,
                                                                                     encoder.preset,
                                                                                     rendition.crf,
                                                                                     outputPath,
                                                                                     encoderOptions,
                                                                                     scaler)

    return outputRenditions


def getOptionsFfmpegString(options):
    ffmpegString = ""
    for optionKey, optionValue in options.items():
        ffmpegString += "-{0} {1} ".format(optionKey, optionValue)
    return ffmpegString


def getOutputFilePath(rendition, video, encoder, scaler):
    muxingFormat = "mkv"
    outputFileName = "{0}_scale={1}_CRF={2}_{4}_{5}_{6}.{3}".format(os.path.splitext(ntpath.basename(video))[0],
                                                                rendition.scaling_size, rendition.crf,
                                                                muxingFormat, encoder.encoderString, encoder.preset, scaler)

    outputPath = "{0}/{1}_{2}x/{3}".format(OUTPUT_SEGMENTS, scaler, rendition.scaling_size, outputFileName)
    return outputPath


# TODO avg mem always 0
def getTimeOfCommand(command):
    timeCommand = "/usr/bin/time -f \"\\t%e \\t%P \\t%M \\t%K\" " + command
    return timeCommand


# Runs the /usr/bin/time command and returns the elapsed time in seconds, the cpu usage in % and the max and avg memory used in kb
def executeTimeCommand(timeCommand):
    err, out = runCommand(timeCommand)

    print(err)
    # print(out)

    err = err.split()
    data = err[-4:]

    realTimeFactor = 0
    elapsedTimeInSeconds = float(data[0])
    cpuUsageInPercent = int(data[1][:-1])
    maxMemUsedInKb = int(data[2])
    avgMemUsedInKb = int(data[3])
    processMonitorResult = ProcessMonitorResult(elapsedTimeInSeconds, cpuUsageInPercent, maxMemUsedInKb, avgMemUsedInKb,
                                                realTimeFactor)

    return processMonitorResult


def getRealTimeFactor(realTimeFactorString):
    if realTimeFactorString.count("speed=") >= 1:
        realtimeFactor = realTimeFactorString[len("speed="):-len("x")]
    else:
        realtimeFactor = realTimeFactorString[:-1]

    return float(realtimeFactor)


# Get the bitrate of a video in Mbit/s and the psnr ( quality metric )
def getBitrateOfVideo(reference, distorted):
    # ffmpegQualityMetricCommand = "ffmpeg_quality_metrics -s lanczos {1} {0} --enable-vmaf --model-path /usr/local/share/model/vmaf_v0.6.1.pkl".format(reference, distorted)
    # #ffmpegQualityMetricCommand = "ffmpeg_quality_metrics -s lanczos {1} {0}".format(reference, distorted)
    # err, out = runCommand(ffmpegQualityMetricCommand)
    # resp = json.loads(out)
    #
    # psnrAverage = (resp["global"]["psnr"]["average"])
    # vmafAverage = (resp["global"]["vmaf"]["average"])

    ffprobeCommand = "ffprobe -hide_banner -loglevel quiet  -show_entries format=duration,bit_rate -of json {0}".format(
        distorted)
    err, out = runCommand(ffprobeCommand)
    resp = json.loads(out)
    bitrateInBps = resp["format"]["bit_rate"]
    bitrateInMbps = int(bitrateInBps) / 1000000.0
    return bitrateInMbps, 0, 0


def runCommand(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    print(err)
    print(out)

    err = err.decode("utf-8")
    # out = out.decode("utf-8")
    return err, out


main(input)
