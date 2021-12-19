"""
Program Simple Media player using Python vlc Module
@author : PG

"""
import sys
import platform
import os
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtCore,QtWidgets,QtGui
from PyQt5.QtWidgets import QMessageBox
import vlc
import time as time_py
import csv


csv_file_name = ""
csv_file_extension = ""
csv_ready = False
colorList = ["r", "b", "y", "k", "g", "m", QtGui.QColor(200, 200, 200), QtGui.QColor(100, 9, 100), QtGui.QColor(150, 123, 165)]
locationLbl = ['gFx', 'gFy', 'gFz', 'wx', 'wy', 'wz', 'Bx', 'By', 'Bz']



time = gFx = gFy = gFz = wx = wy = wz = bx = by = bz = list()
org_time = org_gFx = org_gFy = org_gFz = org_wx = org_wy = org_wz = org_bx = org_by = org_bz = org_labels = list()

recTableLabels = list()

forward_csv_sec = 0
forward_ms = 0
total_ms = 0 #mp4 length
play_total_ms = 0

highLightLabelRange = list()
graphLayoutList = list()
tableWidget = None
labelList = list()

class GraphLayout():
    def __init__(self):
        global locationLbl, highLightLabelRange, forward_csv_sec, labelList

        self.line = pg.InfiniteLine( pos=forward_csv_sec, angle=90, pen='r', movable=False )
        self.graphVBoxLayout = QtWidgets.QVBoxLayout()
        self.chkHBoxLayout = QtWidgets.QHBoxLayout()
        self.labelInputLayout = QtWidgets.QHBoxLayout()

        self.list_checkWidget = list()
        self.checkedList = list()
        self.region = list()
        self.graphWidget = pg.PlotWidget(pen = "r")

        self.highlightWidgets = list()

        self.graphWidget.setMinimumHeight(300)

        for i, v in enumerate(locationLbl):
            qCheckBox = QtWidgets.QCheckBox(v)
            self.list_checkWidget.append(qCheckBox)
            self.chkHBoxLayout.addWidget(self.list_checkWidget[i])
            qCheckBox.stateChanged.connect(self.checkboxChanged)
        self.list_checkWidget[0].setChecked(True)

        self.comboBoxLabel = QtWidgets.QComboBox()
        self.comboBoxLabel.setMaximumWidth(150)
        self.comboBoxLabel.setMaximumHeight(25)
        self.comboBoxLabel.setFont(QtGui.QFont("", 12))
        self.comboBoxLabel.addItems(labelList)


        self.buttonLabel = QtWidgets.QPushButton("ラベル追加")
        self.buttonLabel.setMaximumWidth(100)
        self.buttonLabel.setFont(QtGui.QFont("", 12))
        self.buttonLabel.clicked.connect(self.inputLabelToTable)

        self.buttonRemoveLabel = QtWidgets.QPushButton("ラベル削除")
        self.buttonRemoveLabel.setMaximumWidth(100)
        self.buttonRemoveLabel.setFont(QtGui.QFont("", 12))
        self.buttonRemoveLabel.clicked.connect(self.removeLabel)


        self.labelInputLayout.addWidget(self.comboBoxLabel)
        self.labelInputLayout.addWidget(self.buttonLabel)
        self.labelInputLayout.addWidget(self.buttonRemoveLabel)
        self.labelInputLayout.addWidget(QtWidgets.QLabel(""))

        self.labelSelRange = QtWidgets.QLabel("")
        self.labelSelRange.setMaximumWidth(200)
        self.labelInputLayout.addWidget(self.labelSelRange)

        self.graphVBoxLayout.addWidget(self.graphWidget)
        self.graphVBoxLayout.addLayout(self.labelInputLayout)
        self.graphVBoxLayout.addLayout(self.chkHBoxLayout)

        # emit checkbox changed event automatically
        # don't need to call drawGraph here
        # self.drawGraph()

    def addHighlightRegion(self, begin_time, end_time):
        lr = pg.LinearRegionItem(values=(begin_time, end_time), brush=pg.mkBrush(150,150,150,100), movable=False )
        self.highlightWidgets.append(lr)
        self.graphWidget.addItem(lr)

    def removeHighlightRegion(self, index):
        lr = self.highlightWidgets[index]
        self.graphWidget.removeItem(lr)
        self.highlightWidgets.pop(index)


    def removeLabel(self):
        global tableWidget, recTableLabels
        if len(tableWidget.selectedIndexes()) == 0 :
            return

        selectedRow = tableWidget.currentRow()
        recTableLabels.pop(selectedRow)
        highLightLabelRange.pop(selectedRow)
        tableWidget.removeRow(selectedRow)
        for i,v in enumerate(graphLayoutList):
            v.removeHighlightRegion(selectedRow)

    #click buttonLabel
    def inputLabelToTable(self):
        global org_time, org_labels, highLightLabelRange, graphLayoutList
        global tableWidget, labelList, recTableLabels

        if len(self.region) != 2:
            return
        selLabelIndex = self.comboBoxLabel.currentIndex()
        selLabelText = self.comboBoxLabel.currentText()

        begin_time = self.region[0]
        end_time = self.region[1]

        start_index = -1
        end_index = -1
        for i in range(len(org_time)):
            if org_time[i] >= begin_time and org_time[i] <= end_time and start_index < 0:
                start_index = i
                continue
            if org_time[i] >= begin_time and org_time[i] <= end_time and start_index >= 0 :
                # for labelIdx in range(len(labelList)):
                #     org_labels[labelIdx][i] = 0
                # org_labels[selLabelIndex][i] = 1
                end_index = i

        recTableLabels.append( (selLabelIndex, start_index, end_index) )

        highLightLabelRange.append((selLabelText, begin_time, end_time))

        for i,v in enumerate(graphLayoutList):
            v.addHighlightRegion(begin_time, end_time)

        rowPosition = tableWidget.rowCount()
        tableWidget.insertRow(rowPosition)
        tableWidget.setItem(rowPosition , 0, QtWidgets.QTableWidgetItem(selLabelText))
        tableWidget.setItem(rowPosition , 1, QtWidgets.QTableWidgetItem(str('{:.3f}'.format(begin_time))))
        tableWidget.setItem(rowPosition , 2, QtWidgets.QTableWidgetItem(str('{:.3f}'.format(end_time))))

    def drawGraph(self):
        self.checkedList.clear()
        for i, v in enumerate(self.list_checkWidget):
            if v.checkState():
                self.checkedList.append(i)
        if csv_ready:
            self.gen_graph()

    def drawHighlight(self):
        global highLightLabelRange
        for i,v in enumerate(highLightLabelRange):
            self.addHighlightRegion(v[1], v[2])


    def getLayout(self):
        return self.graphVBoxLayout

    def checkboxChanged(self):
        self.drawGraph()

    def deleteWidget(self):
        global locationLbl

        self.list_checkbox = list()
        self.graphWidget.setParent(None)
        self.graphWidget.clear()

        self.line.setParent(None)
        self.line.deleteLater()

        while self.chkHBoxLayout.count():
            item = self.chkHBoxLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.chkHBoxLayout.setParent(None)

        while self.labelInputLayout.count():
            item = self.labelInputLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.labelInputLayout.setParent(None)



    def gen_graph(self):
        global csv_file_name, csv_file_extension, colorList, locationLbl

        self.graphWidget.clear()
        legend = self.graphWidget.addLegend()
        self.locationList = [gFx, gFy, gFz, wx, wy, wz, bx, by, bz]

        legend.setBrush(pg.mkBrush(0,200,0,50))
        legend.setPen(pg.mkPen(255,0,0,100))
        # self.graphWidget.setXRange(0,1)
        self.graphWidget.showGrid(x=True,y=True)
        for i, v in enumerate(self.checkedList):
            self.graphWidget.plot( pen=colorList[v], name=locationLbl[v])
            self.graphWidget.plot(pen=colorList[v]).setData(time,self.locationList[v])



        self.lr = pg.LinearRegionItem([0, 10])
        self.graphWidget.addItem(self.lr)

        self.lr.sigRegionChanged.connect(self.updateRegion)

        self.drawHighlight()
        self.graphWidget.addItem(self.line)


    def updateRegion(self):
        self.region = self.lr.getRegion()
        self.labelSelRange.setText("[ "+ str('{:.3f}'.format(self.region[0]))+", "+str('{:.3f}'.format(self.region[1]))+" ]")



class Application(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self,parent)
        self.setWindowTitle("動画再生グラフ表示ツール")

        self.loadLabelFromFile()
        #create a simple Instance

        self.Vlc_Instance=vlc.Instance()
        self.Media=None
        #creating empty vlc media Player
        self.MPlayer=self.Vlc_Instance.media_player_new()


        #Initalize the user interface
        self.initUI()
        #Pause var for check if song is in pause mode or not !
        # self.Is_Vframe_Hidden=False

    def loadLabelFromFile(self):
        global labelList, org_labels, recTableLabels
        org_labels = list()
        labelList = list()
        recTableLabels = list()
        f = open("settings.csv", 'r', encoding="utf-8")
        for line in f.readlines():
            labelList.append(line.strip())
            org_labels.append(list())


    def add_graph(self):
        global graphLayoutList
        graphLayout0 = GraphLayout()
        graphLayoutList.append(graphLayout0)
        self.graphsVboxLayout.addLayout(graphLayout0.getLayout())

    def remove_graph(self):
        global graphLayoutList

        if len(graphLayoutList) < 2:
            return

        lastGraphLayout = graphLayoutList.pop()
        lastGraphLayout.deleteWidget()
        self.graphsVboxLayout.removeItem(lastGraphLayout.getLayout())



    def initUI(self):
        global tableWidget
        # print(platform.system())
        """
        Creating a Centeral Widget That's Hold The child widgets such as button ,slider etc..
        """
        self.csvFilePath = None
        self.widget=QtWidgets.QWidget(self)
        #set it as centeral widget element
        self.setCentralWidget(self.widget)
        #self.widget.setToolTip("hai")

        #main vertical layout
        self.mainVBoxLayout = QtWidgets.QVBoxLayout()
        #horizontal layout include selecting mp4 and csv button
        self.hboxButtonLayout = QtWidgets.QHBoxLayout()
        #second horizontal layout include video frame and graph
        self.mainHBoxLayout = QtWidgets.QHBoxLayout()
        #third horizontal layout include play and stop button
        self.btnHBoxLayout = QtWidgets.QHBoxLayout()

        #select btns
        self.selMp4Btn = QtWidgets.QPushButton("開く(動画)")
        self.selMp4Btn.setFont(QtGui.QFont("", 12))
        self.selMp4Btn.clicked.connect(self.open_file)
        self.selMp4Btn.setMaximumWidth(100)
        self.mp4PathLbl = QtWidgets.QLabel("")
        self.selCsvBtn = QtWidgets.QPushButton("開く(CSV)")
        self.selCsvBtn.setFont(QtGui.QFont("", 12))
        self.selCsvBtn.clicked.connect(self.open_csv_file)
        self.csvPathLbl = QtWidgets.QLabel("")
        self.selCsvBtn.setMaximumWidth(100)
        self.hboxButtonLayout.addWidget(self.selMp4Btn)
        self.hboxButtonLayout.addWidget(self.mp4PathLbl)
        self.hboxButtonLayout.addWidget(self.selCsvBtn)
        self.hboxButtonLayout.addWidget(self.csvPathLbl)

        self.buttonSaveCsv = QtWidgets.QPushButton("CSV保存")
        self.buttonSaveCsv.setFont(QtGui.QFont("", 12))
        self.buttonSaveCsv.clicked.connect(self.save_csv_file)
        self.buttonSaveCsv.setMaximumWidth(100)
        self.hboxButtonLayout.addWidget(self.buttonSaveCsv)

        #main layout elements
            #videolayout and its elements
        self.videoVBoxLayout = QtWidgets.QVBoxLayout()
         #Creating Vedio Frame element whichs shows the each frame of the vedio
            # In this widget, the video will be drawn
        if platform.system() == "Darwin": # for MacOS
            self.VideoFrame = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self.VideoFrame = QtWidgets.QFrame()

            #just for QFrame to customize [setting the color ]
        self.Pallet=self.VideoFrame.palette()
        self.Pallet.setColor(QtGui.QPalette.Window,QtGui.QColor(0, 9, 0))
        self.VideoFrame.setPalette(self.Pallet)
        self.VideoFrame.setAutoFillBackground(True)
            #Slider Setup
        self.MSlider=QtWidgets.QSlider(QtCore.Qt.Horizontal,self)
        self.MSlider.setMaximum(1000)
            #need to add slider postion update fun
        self.MSlider.sliderMoved.connect(self.set_position)
        self.MSlider.sliderPressed.connect(self.set_position)
        # self.MSlider.valueChanged.connect(self.set_position)

            #label layout and its elements
        self.TimeLblHLayout = QtWidgets.QHBoxLayout()
        self.Time_duration=QtWidgets.QLabel("00:00:0")
        self.Video_Length=QtWidgets.QLabel("00:00:0")
        font = self.font()
        font.setPointSize(24)
        self.Video_Length.setFont(font)
        self.Time_duration.setFont(font)
        # self.
        self.TimeLblHLayout.addWidget(self.Time_duration)
        # self.TimeLblHLayout.addSpacing(200)
        self.TimeLblHLayout.addStretch(1)
        self.TimeLblHLayout.addWidget(self.Video_Length)

        #timeZeroMathLayout
        self.timeZeroMathLayout = QtWidgets.QHBoxLayout()

        self.textboxSetZero = QtWidgets.QTextEdit("0")
        self.textboxSetZero.setFont(QtGui.QFont("", 12))
        self.textboxSetZero.setMaximumWidth(50)
        self.textboxSetZero.setMaximumHeight(30)

        self.buttonSetZero = QtWidgets.QPushButton("オフセット")
        self.buttonSetZero.setFont(QtGui.QFont("", 12))
        self.buttonSetZero.setMaximumWidth(100)
        self.buttonSetZero.clicked.connect(self.setZeroMatch)

        self.textboxSetZeroForVideo = QtWidgets.QTextEdit("0")
        self.textboxSetZeroForVideo.setFont(QtGui.QFont("", 12))
        self.textboxSetZeroForVideo.setMaximumWidth(50)
        self.textboxSetZeroForVideo.setMaximumHeight(30)

        self.buttonSetZeroForVideo = QtWidgets.QPushButton("0秒合わせ(動画)")
        self.buttonSetZeroForVideo.setFont(QtGui.QFont("", 12))
        self.buttonSetZeroForVideo.setMaximumWidth(120)
        self.buttonSetZeroForVideo.clicked.connect(self.setZeroMatchForVideo)


        self.timeZeroMathLayout.addWidget(QtWidgets.QLabel(""))

        self.timeZeroMathLayout.addWidget(self.textboxSetZeroForVideo)
        labelSecondVideo = QtWidgets.QLabel("秒")
        labelSecondVideo.setFont(QtGui.QFont("", 12))
        labelSecondVideo.setMaximumWidth(15)
        self.timeZeroMathLayout.addWidget(labelSecondVideo)
        self.timeZeroMathLayout.addWidget(self.buttonSetZeroForVideo)
        self.timeZeroMathLayout.addSpacing(50)


        self.timeZeroMathLayout.addWidget(self.textboxSetZero)
        labelSecond = QtWidgets.QLabel("秒")
        labelSecond.setFont(QtGui.QFont("", 12))
        labelSecond.setMaximumWidth(15)
        self.timeZeroMathLayout.addWidget(labelSecond)
        self.timeZeroMathLayout.addWidget(self.buttonSetZero)


        self.videoVBoxLayout.addWidget(self.VideoFrame,6)
        self.videoVBoxLayout.addSpacing(50)
        self.videoVBoxLayout.addWidget(self.MSlider,1)
        self.videoVBoxLayout.addLayout(self.TimeLblHLayout,2)

        self.videoVBoxLayout.addLayout(self.timeZeroMathLayout,3)
        #graphlayout and its elements

        self.rightVboxLayout = QtWidgets.QVBoxLayout()
        self.graphNumButtonLayout = QtWidgets.QHBoxLayout()

        self.graphsVboxLayout = QtWidgets.QVBoxLayout()


        # self.graphVBoxLayout = QtWidgets.QVBoxLayout()
        pg.setConfigOption('background', '#ffffff')
        # self.graphWidget = pg.PlotWidget(pen = "r")


        # Add Graph Button
        self.addGraphBtn = QtWidgets.QPushButton("グラフ追加")
        self.addGraphBtn.setFont(QtGui.QFont("", 12))
        self.addGraphBtn.setMaximumWidth(100)
        self.addGraphBtn.clicked.connect(self.add_graph)

        # Remove Graph Button
        self.removeGraphBtn = QtWidgets.QPushButton("グラフ削除")
        self.removeGraphBtn.setFont(QtGui.QFont("", 12))
        self.removeGraphBtn.setMaximumWidth(100)
        self.removeGraphBtn.clicked.connect(self.remove_graph)

        self.add_graph()

        self.graphNumButtonLayout.addWidget(self.addGraphBtn)
        self.graphNumButtonLayout.addSpacing(30)
        self.graphNumButtonLayout.addWidget(self.removeGraphBtn)
        self.graphNumButtonLayout.addSpacing(30)
        self.graphNumButtonLayout.addWidget(QtWidgets.QLabel(""))

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        tableWidget.setFont(QtGui.QFont("", 12))
        tableWidget.setMaximumHeight(200)
        tableWidget.setColumnCount(3)
        tableWidget.setHorizontalHeaderLabels(['ラベル', '開始', '終了'])

        widget = QtWidgets.QWidget(self)
        widget.setLayout(self.graphsVboxLayout)

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidget(widget)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.rightVboxLayout.addLayout(self.graphNumButtonLayout)
        self.rightVboxLayout.addWidget(self.scrollArea)
        # self.rightVboxLayout.addLayout(self.graphsVboxLayout)
        self.rightVboxLayout.addWidget(tableWidget)

        #add layouts to mainHbox

        self.mainHBoxLayout.addLayout(self.videoVBoxLayout,1)
        self.mainHBoxLayout.addLayout(self.rightVboxLayout,1)

        # self.mainHBoxLayout.addLayout(self.graphVBoxLayout,1)

        #btn layout

        #Play Button
        self.buttonPlay=QtWidgets.QPushButton("再生")
        self.buttonPlay.setFont(QtGui.QFont("", 12))
        self.btnHBoxLayout.addWidget(self.buttonPlay)
        self.buttonPlay.clicked.connect(self.play_pause)


        #stop Button
        self.buttonStop=QtWidgets.QPushButton("停止")
        self.buttonStop.setFont(QtGui.QFont("", 12))
        self.btnHBoxLayout.addWidget(self.buttonStop)
        self.buttonStop.clicked.connect(self.Stop)

        self.btnHBoxLayout.addStretch(1)

        #add layouts to widget
        self.mainVBoxLayout.addLayout(self.hboxButtonLayout)
        self.mainVBoxLayout.addLayout(self.mainHBoxLayout)
        self.mainVBoxLayout.addLayout(self.btnHBoxLayout)
        self.widget.setLayout(self.mainVBoxLayout)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(50)
        self.time=QtCore.QTime(0,0,0)
        self.timer.timeout.connect(self.timerEvent)
        self.timer.timeout.connect(self.update_ui)
        self.VideoFrame.setStyleSheet ( "background-color: rgb(200, 100, 255)" )
        self.setGeometry(0,0,1780,800)


    #Play and pause method where media can pause and resume
    def play_pause(self):
        global csv_ready, total_ms, play_total_ms
        """Toggle play/pause status
        """
        # print(self.csv_ready)
        if csv_ready == False:
            return
        if self.MPlayer.is_playing():
            self.MPlayer.pause()
            self.buttonPlay.setText("再生")
            self.is_paused = True
            self.timer.stop()
        else:
            if csv_ready == True:
                # self.gen_graph_html()
                self.MPlayer.play()
                if self.is_stopped == True:
                    time_py.sleep(1)
                    self.is_stopped = False
                    total_ms = self.MPlayer.get_length()

                    play_total_ms = total_ms - forward_ms

                    self.MSlider.setMaximum(play_total_ms)
                    self.MPlayer.set_position( forward_ms / total_ms )

                self.buttonPlay.setText("一時停止")
                self.is_paused = False
                self.timer.start()


            else:
                self.open_csv_file()

    #Stop Media Player
    def Stop(self):
        global forward_ms, total_ms
        """
            Stop player
        """
        self.MPlayer.stop()
        self.buttonPlay.setText("再生")
        self.timer.stop()
        self.is_stopped = True
        self.MSlider.setValue(0)


        # if self.Is_Vframe_Hidden:
        #     self.VideoFrame.show()
        #     self.Is_Vframe_Hidden=False
        #     self.resize(1024,768)

    def initData(self):
        global graphLayoutList, tableWidget, highLightLabelRange
        #global org_time,org_gFx,org_gFy,org_gFz,org_wx,org_wy,org_wz,org_bx,org_by,org_bz,org_label

        global csv_ready

        tableWidget.setRowCount(0)

        while(len(graphLayoutList)>1):
            lastGraphLayout = graphLayoutList.pop()
            lastGraphLayout.deleteWidget()
            self.graphsVboxLayout.removeItem(lastGraphLayout.getLayout())

        # highLightLabelRange.clear()

        graphLayout = graphLayoutList[0]

        graphLayout.graphWidget.clear()

        highLightLabelRange.clear()

        csv_ready = False

        self.csvPathLbl.setText("")

        self.loadLabelFromFile()

        # graphLayout.line.setParent(None)
        # graphLayout.line.deleteLater()
        # graphLayout.graphWidget.clear()

        # while self.chkHBoxLayout.count():
        #     item = self.chkHBoxLayout.takeAt(0)
        #     widget = item.widget()
        #     if widget is not None:
        #         widget.deleteLater()
        # self.chkHBoxLayout.setParent(None)




    def open_csv_file(self):
        global time,gFx,gFy,gFz,wx,wy,wz,bx,by,bz,csv_ready,csv_file_name,csv_file_extension, org_time, org_gFx, org_gFy, org_gFz, org_wx, org_wy, org_wz, org_bx, org_by, org_bz, org_labels, labelList
        global graphLayoutList, tableWidget, highLightLabelRange, recTableLabels

        self.initData()

        sel_csv_text = "Choose CSV File"
        self.csvFilePath = QtWidgets.QFileDialog.getOpenFileName(self, sel_csv_text, os.path.expanduser('~'))
        if self.csvFilePath[0]!= "":
            csv_file_name,csv_file_extension=os.path.splitext(self.csvFilePath[0])
            # print(self.csv_file_extension)
            if(csv_file_extension == ".csv" or csv_file_extension == ".CSV"):
                self.csvPathLbl.setText(csv_file_name+csv_file_extension)
                df = pd.read_csv(csv_file_name+csv_file_extension, encoding = "shift_jis")

                org_time = list(df["time"])
                org_gFx = list(df["gFx"])
                org_gFy = list(df["gFy"])
                org_gFz = list(df["gFz"])
                org_wx = list(df["wx"])
                org_wy = list(df["wy"])
                org_wz = list(df["wz"])
                org_bx = list(df["Bx"])
                org_by = list(df["By"])
                org_bz = list(df["Bz"])

                highLightLabelRange.clear()
                recTableLabels.clear()

                try:
                    for idx, label in enumerate(labelList):
                        org_labels[idx] = list(df[label])

                    begin_time = 0
                    end_time = 0
                    start_index = 0
                    end_index = 0

                    add_label = False
                    for label_idx, label_name in enumerate(labelList):
                        for i in range(len(org_time)):
                            if int(org_labels[label_idx][i]) != 1 and  add_label == True :
                                end_index = i-1
                                end_time = org_time[end_index]
                                highLightLabelRange.append([labelList[label_idx], begin_time, end_time])
                                recTableLabels.append((label_idx, start_index, end_index))

                                add_label = False
                                continue
                            if int(org_labels[label_idx][i]) == 1 and add_label == False:
                                start_index = i
                                begin_time = org_time[start_index]
                                add_label = True
                                continue
                        if len(org_time) > 0 and add_label == True:
                                highLightLabelRange.append([labelList[label_idx], begin_time, org_time[len(org_time)-1]])
                                recTableLabels.append((label_idx, start_index, len(org_time)-1))
                except:
                    # for idx, label in enumerate(labelList):
                    #     for i in range(len(org_time)):
                    #         org_labels[idx].append(0)
                    print("ERROR")

                time = org_time.copy()
                gFx = org_gFx.copy()
                gFy = org_gFy.copy()
                gFz = org_gFz.copy()
                wx = org_wx.copy()
                wy = org_wy.copy()
                wz = org_wz.copy()
                bx = org_bx.copy()
                by = org_by.copy()
                bz = org_bz.copy()

                csv_ready = True

                for i, v in enumerate(graphLayoutList):
                    v.drawGraph()

                tableWidget.setRowCount(0)
                for i, v in enumerate(highLightLabelRange):
                    rowPosition = tableWidget.rowCount()
                    tableWidget.insertRow(rowPosition)
                    tableWidget.setItem(rowPosition , 0, QtWidgets.QTableWidgetItem(str(v[0])))
                    tableWidget.setItem(rowPosition , 1, QtWidgets.QTableWidgetItem(str('{:.3f}'.format(float(v[1])))))
                    tableWidget.setItem(rowPosition , 2, QtWidgets.QTableWidgetItem(str('{:.3f}'.format(float(v[2])))))

            else:
                csv_ready = False
                self.csvPathLbl.setText("incorrect extension")

    # def getIdx(self, rowIdx):
    #     global org_labels
    #     try:
    #         for i in range(len(org_labels)):
    #             if int(org_labels[i][rowIdx]) == 1:
    #                 return i
    #     except:
    #         return -1
    #     return -1



    def save_csv_file(self):
        global labelList
        if self.csvFilePath == None:
            return
        csvSavePath = self.csvFilePath[0]
        index = csvSavePath.find('.csv')
        csvSavePath = csvSavePath[:index] + '_labeled' + csvSavePath[index:]
        with open(csvSavePath,'w', encoding='shift_jis', newline='') as f:
            writer = csv.writer(f)
            header = ['time','gFx', 'gFy', 'gFz', 'wx', 'wy', 'wz', 'Bx', 'By', 'Bz']
            for label in labelList:
                header.append(label)

            writer.writerow(header)
            for i in range(len(org_time)):
                if org_time[i]-forward_csv_sec < 0:
                    continue
                gFx = org_gFx[i]
                gFy = org_gFy[i]
                gFz = org_gFz[i]
                wx = org_wx[i]
                wy = org_wy[i]
                wz = org_wz[i]
                bx = org_bx[i]
                by = org_by[i]
                bz = org_bz[i]

                if pd.isna(org_gFx[i]):
                    gFx = ""
                if pd.isna(org_gFy[i]):
                    gFy = ""
                if pd.isna(org_gFz[i]):
                    gFz = ""
                if pd.isna(org_wx[i]):
                    wx = ""
                if pd.isna(org_wy[i]):
                    wy = ""
                if pd.isna(org_wz[i]):
                    wz = ""
                if pd.isna(org_bx[i]):
                    bx = ""
                if pd.isna(org_by[i]):
                    by = ""
                if pd.isna(org_bz[i]):
                    bz = ""
                data = [org_time[i]-forward_csv_sec, gFx, gFy, gFz, wx, wy, wz, bx, by, bz]

                self.recTableToCsv()

                for idx in range(len(labelList)):
                    if pd.isna(org_labels[idx][i]):
                        data.append(0)
                    else:
                        data.append(org_labels[idx][i])
                writer.writerow(data)
        QMessageBox.information(None, "", "CSV保存完了しました", QMessageBox.Yes)

    def recTableToCsv(self):
        global labelList, org_time, org_labels, recTableLabels
        for idx, label in enumerate(labelList):
            org_labels[idx] = list()
            for i in range(len(org_time)):
                org_labels[idx].append(0)
        
        for idx, label_data in enumerate(recTableLabels):
            for i in range(label_data[1], label_data[2]+1):
                org_labels[label_data[0]][i] = 1




    def open_file(self):
        """
            Open a media file in a MPlayer
        """

        dialog_txt = "Choose Media File"
        filename = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'))
        #check if anything got if not empty just pass else return
        if filename[0]!= "":
            #before returning if it's an audio file resize the media player
            self.filename,self.file_extension=os.path.splitext(filename[0])
            self.mp4PathLbl.setText(self.filename+self.file_extension)
            self.is_stopped = True
            self.VideoFrame.show()
        else:
            return


        # getOpenFileName returns a tuple, so use only the actual file name
        self.media = self.Vlc_Instance.media_new(filename[0])

        # Put the media in the media player
        self.MPlayer.set_media(self.media)

        # Parse the metadata of the file
        self.media.parse()

        # Set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in it's own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        if platform.system() == "Linux": # for Linux using the X Server
            self.MPlayer.set_xwindow(int(self.VideoFrame.winId()))
        elif platform.system() == "Windows": # for Windows
            self.MPlayer.set_hwnd(int(self.VideoFrame.winId()))
        elif platform.system() == "Darwin": # for MacOS
            self.MPlayer.set_nsobject(int(self.VideoFrame.winId()))


    # Match zero for video
    def setZeroMatchForVideo(self):
        global time, gFx, gFy, gFz, wx, wy, wz, bx, by, bz, org_time, org_gFx, org_gFy, org_gFz, org_wx, org_wy, org_wz, org_bx, org_by, org_bz
        global forward_ms, total_ms, play_total_ms

        if csv_ready == False:
            return

        if self.MPlayer.is_playing():
            self.timer.stop()

        try:
            sec = float(self.textboxSetZeroForVideo.toPlainText())
        except:
            print('The variable is not a number')
            self.textboxSetZero.setText("0")
            sec = 0.0

        if sec < 0 :
            self.textboxSetZeroForVideo.setText("0")
            sec = 0.0

        forward_ms = sec * 1000

        play_total_ms = total_ms - forward_ms
        self.MSlider.setMaximum(play_total_ms)
        self.MSlider.setValue(0)
        if self.is_stopped == False:
            if total_ms >0 :
                self.MPlayer.set_position( forward_ms / total_ms )
            self.timer.start()

    # Match zero for csv
    def setZeroMatch(self):
        global time, gFx, gFy, gFz, wx, wy, wz, bx, by, bz, org_time, org_gFx, org_gFy, org_gFz, org_wx, org_wy, org_wz, org_bx, org_by, org_bz
        global total_ms, play_total_ms, forward_csv_sec
        global graphLayoutList
        if csv_ready == False:
            return

        if self.MPlayer.is_playing():
            self.timer.stop()

        try:
            sec = float(self.textboxSetZero.toPlainText())
        except:
            print('The variable is not a number')
            self.textboxSetZero.setText("0")
            sec = 0.0

        if sec < 0 :
            self.textboxSetZero.setText("0")
            sec = 0.0

        forward_csv_sec = sec

        for i,v in enumerate(graphLayoutList):
            v.line.setValue(forward_csv_sec)



        if self.MPlayer.is_playing():
            self.Stop()



    def update_ui(self):
        global total_ms, forward_ms
        """Updates the user interface"""

        # Set the slider's position to its corresponding media position
        # Note that the setValue function only takes values of type int,
        # so we must first convert the corresponding media position.

        cur_pos = self.MPlayer.get_position()

        self.MSlider.setValue(int(cur_pos*total_ms) - forward_ms)

        # No need to call this function if nothing is played
        if not self.MPlayer.is_playing():
            self.timer.stop()

            # After the video finished, the play button stills shows "Pause",
            # which is not the desired behavior of a media player.
            # This fixes that "bug".
            if not self.is_paused:
                self.Stop()


    def set_position(self):
        global forward_ms, total_ms
        """Set the movie position according to the position slider.
        """

        # The vlc MPlayer needs a float value between 0 and 1, Qt uses
        # integer variables, so you need a factor; the higher the factor, the
        # more precise are the results (1000 should suffice).

        # Set the media position to where the slider was dragged
        # print(self.MSlider.value())
        self.timer.stop()

        pos = self.MSlider.value()
        self.MPlayer.set_position( (pos + forward_ms) / total_ms )

        self.timer.start()

    def convertTime(self, ms):
        subsec = (int(ms/100)) %10
        second = (int(ms/1000)) % 60
        minute = (int(ms/1000/60)) % 60
        retTime = ""

        if second < 10 :
            second = "0" + str(second)

        if minute < 10 :
            minute = "0" + str(minute)

        return str(minute) + ":" + str(second) + ":" + str(subsec)

    def timerEvent(self):
        global forward_ms, total_ms, play_total_ms, forward_csv_sec
        global graphLayoutList

        cur_ms = self.MPlayer.get_position() * total_ms
        #Current Position in ms

        for i,v in enumerate(graphLayoutList):
            v.line.setValue( ( cur_ms- forward_ms )/1000 + forward_csv_sec)

        self.Time_duration.setText(self.convertTime(cur_ms - forward_ms))
        self.Video_Length.setText(self.convertTime(play_total_ms))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    player = Application()
    player.show()
    player.resize(1024,768)
    sys.exit(app.exec_())