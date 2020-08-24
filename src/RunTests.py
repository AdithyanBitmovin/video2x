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
    def __init__(self, width, height, bitrate):
        self.width = width
        self.height = height
        self.bitrateInMbits = bitrate


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
        "https://storage.googleapis.com/adi-hardware-testing/input/jellyfish-120-mbps-4k-uhd-hevc.mkv"
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
    if (testType == "software_x264"):
        logging.info("Evaluating X264 - Software Encoder")
        testCase = getTestCase_x264()
    elif (testType == "hardware_h264nvenc"):
        logging.info("Evaluating H264-NVENC - Nvidia Hardware Encoder")
        testCase = getTestCase_h264nvenc()
    elif (testType == "software_x265"):
        logging.info("Evaluating X265 - Software Encoder")
        testCase = getTestCase_x265()
    elif (testType == "hardware_hevcnvenc"):
        logging.info("Evaluating H265-NVENC - Nvidia Hardware Encoder")
        testCase = getTestCase_hevcnvenc()
    else:
        logging.info("Evaluating X264 - Software Encoder")
        testCase = getTestCase_x265()

    evalTestData(videos, testCase)


def writeOutputToFile(jsonPrettyString, encoder, dateTimeForFileOutput):
    rcLookahead = ""
    if bool(encoder.encoderOptions):
        rcLookahead = "_rc"

    outputFilePath = "{0}/{1}_{2}_{3}{4}.json".format(OUTPUT_RESULTS, dateTimeForFileOutput,
                                                       encoder.encoderString, encoder.preset, rcLookahead)

    resultsFile = open(outputFilePath, "w")
    resultsFile.write(jsonPrettyString)
    resultsFile.close()
    return outputFilePath


def prettifyJsonString(results):
    jsonData = str(results).replace("\'", "\"")
    jsonObject = json.loads(jsonData)
    jsonPrettyString = json.dumps(jsonObject, indent=2)
    return jsonPrettyString


def getTestCase_x264():
    # Initialize encoders
    encoders = []
    x264codecOptionsString = r"""{
        "aud" : "1",
        "bf" : "3",
        "coder" : "1",
        "direct-pred" : "spatial",
        "me_range" : "16",
        "profile" : "high",
        "refs" : "3",
        "x264-params" : "b-adapt=1:me=hex:rc-lookahead=40:subme=7:trellis=1:nal-hrd=none:b-pyramid=normal:partitions=i4x4,i8x8,p8x8,b8x8:open-gop=0:stitchable=1:force-cfr=1:aud=1"
    }"""
    x264codecOptions = json.loads(x264codecOptionsString)
    encoders.append(Encoder("libx264", "slow", x264codecOptions))

    # Intialize renditions
    renditions = []
    renditions.append(Rendition(640, 360, 0.5))
    renditions.append(Rendition(640, 360, 0.7))
    renditions.append(Rendition(960, 360, 1.0))
    renditions.append(Rendition(1280, 720, 4.7))

    # Intialize decoder
    decoder = Decoder("h264", {})

    testCase = TestCase(decoder, encoders, renditions, "scale")
    return testCase

def getTestCase_x265():
    # Initialize encoders
    encoders = []
    x265codecOptionsString = r"""{
       "x265-params" : "log-level=error"
    }"""
    codecOptions = json.loads(x265codecOptionsString)
    encoders.append(Encoder("libx265", "medium", codecOptions))
    # encoders.append(Encoder("libx265", "fast", codecOptions))
    # encoders.append(Encoder("libx265", "faster", codecOptions))
    # encoders.append(Encoder("libx265", "veryfast", codecOptions))
    # encoders.append(Encoder("libx265", "superfast", codecOptions))
    # encoders.append(Encoder("libx265", "ultrafast", codecOptions))

    # Intialize renditions
    renditions = []
    renditions.append(Rendition(3840, 2160, 15.0))
    renditions.append(Rendition(3840, 2160, 12.0))
    renditions.append(Rendition(2560, 1440, 8.0))
    renditions.append(Rendition(2560, 1440, 6.0))
    renditions.append(Rendition(1920, 1080, 4.0))
    renditions.append(Rendition(1280, 720, 2.0))
    renditions.append(Rendition(1280, 720, 1.0))
    renditions.append(Rendition(960, 540, 0.6))

    # Intialize decoder
    decoder = Decoder("hevc", {})

    testCase = TestCase(decoder, encoders, renditions, "scale")
    return testCase


def getTestCase_h264nvenc():
    # Initialize encoders
    encoders = []
    codecOptionsString = r"""{
        "tune" : "hq",
        "rc-lookahead" : "40"
    }"""
    codecOptions = json.loads(codecOptionsString)
    encoders.append(Encoder("h264_nvenc", "p5", {}))
    encoders.append(Encoder("h264_nvenc", "p6", {}))
    encoders.append(Encoder("h264_nvenc", "p7", {}))

    # Intialize renditions
    renditions = []
    renditions.append(Rendition(640, 360, 0.5))
    renditions.append(Rendition(640, 360, 0.7))
    renditions.append(Rendition(960, 360, 1.0))
    renditions.append(Rendition(1280, 720, 4.7))

    # Intialize decoder
    h264CuvidOptionsString = r"""{
        "vsync" : "0",
        "hwaccel" : "cuvid"
    }"""
    h264CuvidOptions = json.loads(h264CuvidOptionsString)
    decoder = Decoder("h264_cuvid", h264CuvidOptions)

    testCase = TestCase(decoder, encoders, renditions, "scale_npp")
    return testCase


def getTestCase_hevcnvenc():
    # Initialize encoders
    encoders = []
    codecOptionsString = r"""{
        "tune" : "hq"
    }"""
    codecOptions = json.loads(codecOptionsString)
    encoders.append(Encoder("hevc_nvenc", "p7", {}))
    # encoders.append(Encoder("hevc_nvenc", "p6", {}))
    # encoders.append(Encoder("hevc_nvenc", "p5", {}))
    # encoders.append(Encoder("hevc_nvenc", "p4", {}))
    # encoders.append(Encoder("hevc_nvenc", "p3", {}))
    # encoders.append(Encoder("hevc_nvenc", "p2", {}))
    # encoders.append(Encoder("hevc_nvenc", "p1", {}))

    # Intialize renditions
    renditions = []
    renditions.append(Rendition(3840, 2160, 15.0))
    renditions.append(Rendition(3840, 2160, 12.0))
    renditions.append(Rendition(2560, 1440, 8.0))
    renditions.append(Rendition(2560, 1440, 6.0))
    renditions.append(Rendition(1920, 1080, 4.0))
    renditions.append(Rendition(1280, 720, 2.0))
    renditions.append(Rendition(1280, 720, 1.0))
    renditions.append(Rendition(960, 540, 0.6))

    # Intialize decoder
    h264CuvidOptionsString = r"""{
        "vsync" : "0",
        "hwaccel" : "cuvid"
    }"""
    h264CuvidOptions = json.loads(h264CuvidOptionsString)
    decoder = Decoder("hevc_cuvid", h264CuvidOptions)

    testCase = TestCase(decoder, encoders, renditions, "scale_npp")
    return testCase


def evalTestData(videos, testCase):
    dateTimeForFileOutput = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    for encoder in testCase.encoders:
        results = []
        for video in videos:
            logging.info(
                "Running tests for: |\t " + video + " \t|\t Decoder: " + testCase.decoder.decoderString +
                " \t|\t Encoder: " + encoder.encoderString + " \t|\t Preset: " + encoder.preset + " \t|")

            encodeCommand = getEncodeCommand(video, testCase.decoder, encoder, testCase.renditions, testCase.scaler)
            print(encodeCommand)

            timeOfCommand = getTimeOfCommand(encodeCommand)
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
                    "vmaf" : vmafList
                }
            )

        jsonPrettyString = prettifyJsonString(results)
        outputFilePath = writeOutputToFile(jsonPrettyString, encoder, dateTimeForFileOutput)
        logging.info("Results written in {0}".format(outputFilePath))


def extractBdMetrics(encoder, testCase, video):
    bitrateOutputList = []
    psnrOutputList = []
    vmafOutputList = []
    for rendition in testCase.renditions:
        outputPath = getOutputFilePath(rendition, video, encoder)
        "{0}/{1}".format(OUTPUT_RESULTS, outputPath)

        sourceInputPath = getInputPath(video)
        bitrateOutput, psnr, vmaf = getBitrateOfVideo(sourceInputPath, outputPath)
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


# Returns the command to encode with the given parameters as a string.
# video - filename
# encoder - x264 / x265
# bitrate in Mbit/s
# preset - slow / fast
def getEncodeCommand(video, decoder, encoder, renditionList, scaler):
    ffmpegPath = "ffmpeg -hide_banner -loglevel quiet -stats"
    inputPath = getInputPath(video)

    decodingOption = "{0} -c:v {1}".format(getOptionsFfmpegString(decoder.decoderOptions), decoder.decoderString)

    outputRenditionsCommand = ""
    for rendition in renditionList:
        outputRenditionsCommand += getRenditionFfmpegSubCommand(encoder, video, rendition, scaler)

    ffmpegCommand = '{0}  -y {1} -i {2} {3}'.format(ffmpegPath, decodingOption, inputPath, outputRenditionsCommand)
    return ffmpegCommand


def getInputPath(video):
    inputPath = INPUT_SOURCE + "/" + video
    return inputPath


def getRenditionFfmpegSubCommand(encoder, video, rendition, scaler):
    outputPath = getOutputFilePath(rendition, video, encoder)
    # outputPath = "-f null /dev/null"

    encoderOptions = getOptionsFfmpegString(encoder.encoderOptions)
    outputRenditions = ' -vf {7}={0}:{1} -c:v {2} -preset {3} {6} -b:v {4}M -an {5}'.format(rendition.width,
                                                                                            rendition.height,
                                                                                            encoder.encoderString,
                                                                                            encoder.preset,
                                                                                            rendition.bitrateInMbits,
                                                                                            outputPath,
                                                                                            encoderOptions,
                                                                                            scaler)

    return outputRenditions


def getOptionsFfmpegString(options):
    ffmpegString = ""
    for optionKey, optionValue in options.items():
        ffmpegString += "-{0} {1} ".format(optionKey, optionValue)
    return ffmpegString


def getOutputFilePath(rendition, video, encoder):
    muxingFormat = "mkv"
    outputFileName = "{0}_{1}_{2}_{3}Mbps_{5}_{6}.{4}".format(os.path.splitext(ntpath.basename(video))[0],
                                                              rendition.height, rendition.width,
                                                              rendition.bitrateInMbits,
                                                              muxingFormat, encoder.encoderString, encoder.preset)
    outputPath = "{0}/{1}".format(OUTPUT_SEGMENTS, outputFileName)
    return outputPath


# TODO avg mem always 0
def getTimeOfCommand(command):
    timeCommand = "/usr/bin/time -f \"\\t%e \\t%P \\t%M \\t%K\" " + command
    return timeCommand


# Runs the /usr/bin/time command and returns the elapsed time in seconds, the cpu usage in % and the max and avg memory used in kb
def executeTimeCommand(timeCommand):
    err, out = runCommand(timeCommand)
    err = err.split()
    data = err[-5:]

    realTimeFactor = getRealTimeFactor(data[0])
    elapsedTimeInSeconds = float(data[1])
    cpuUsageInPercent = int(data[2][:-1])
    maxMemUsedInKb = int(data[3])
    avgMemUsedInKb = int(data[4])
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
    ffmpegQualityMetricCommand = "ffmpeg_quality_metrics -s lanczos {1} {0} --enable-vmaf --model-path /usr/local/share/model/vmaf_v0.6.1.pkl".format(reference, distorted)
    #ffmpegQualityMetricCommand = "ffmpeg_quality_metrics -s lanczos {1} {0}".format(reference, distorted)
    err, out = runCommand(ffmpegQualityMetricCommand)
    resp = json.loads(out)

    psnrAverage = (resp["global"]["psnr"]["average"])
    vmafAverage = (resp["global"]["vmaf"]["average"])

    ffprobeCommand = "ffprobe -hide_banner -loglevel quiet  -show_entries format=duration,bit_rate -of json {0}".format(
        distorted)
    err, out = runCommand(ffprobeCommand)
    resp = json.loads(out)
    bitrateInBps = resp["format"]["bit_rate"]
    bitrateInMbps = int(bitrateInBps) / 1000000.0
    return bitrateInMbps, psnrAverage, vmafAverage


def runCommand(ffmpegCommand):
    proc = subprocess.Popen(ffmpegCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    err = err.decode("utf-8")
    out = out.decode("utf-8")
    return err, out


main(input)
