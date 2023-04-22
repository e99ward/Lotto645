import sys
import time
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QCheckBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QMessageBox, QPlainTextEdit
from PyQt5.QtGui import QTextCursor, QIcon
from LottoDB import LottoDB

nm_in_db = []
# nm_in_db = [ # example
#     { 'draw': 234, 'date': '2022-02-28', 'n': [1, 12, 23, 34, 40, 45], 'bonus': 12 },
#     { 'draw': 235, 'date': '2022-03-02', 'n': [7, 8, 23, 24, 41, 42], 'bonus': 13 }]

class Broker(QThread):

    status = pyqtSignal()
    complete = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.order = False
        self.mode = False
        self.ldb = LottoDB()

    def run(self):
        # Load Lotto DB
        global nm_in_db
        self.ldb.LoadNumbersJSON()
        nm_in_db = self.ldb.numbers
        self.status.emit()
        # Update Lotto DB
        print('checking the newest numbers....')
        updated = self.ldb.CheckUpdate()
        if updated:
            nm_in_db = self.ldb.numbers
            self.status.emit()
        # Run Lotto ML
        from LottoML import LottoML
        self.lml = LottoML()
        nPred = [1,2,3,4,5,6]
        while True:
            if self.order:
                print("start")
                print("loading numbers")
                self.lml.LoadNumbersCSV()
                draw = self.lml.lastdraw
                drawlatest = nm_in_db[-1]['draw']
                runs = draw - drawlatest
                if runs < 0:
                    print("update numbers")
                    for idx in range(runs, 0):
                        self.lml.PassNumbers(nm_in_db[idx]['n'])
                    self.lml.SaveNumbersCSV()
                print("predicting")
                nPred = self.lml.Coordinator(self.mode)
                print('completed!!')
                self.complete.emit(nPred)
                self.order = False
                # break
            time.sleep(3) # magical three seconds
        # print('completed!!')
        # self.complete.emit(nPred)

    def __del__(self):
        print("...end thread")

    @pyqtSlot()
    def DoPrediction(self):
        print("...do prediction")
        self.order = True


class Stream(QObject):

    newText = pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))

    def flush(self):
        self.newText.emit('')


class App(QWidget):

    do_prediction_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.w = None
        self.broker = Broker()
        self.cntMax = len(nm_in_db)
        self.title = 'Lotto 645 - 번호 예측기'
        self.left = 100
        self.top = 100
        self.width = 600
        self.height = 500
        fontD = self.font()
        fontD.setPointSize(10)
        fontD.setFamilies(['나눔바른고딕', '맑은 고딕', 'Segoe UI', 'NanumBarunGothic'])
        self.window().setFont(fontD)
        self.initUI()

    def initUI(self):
        # Load Lotto DB
        self.broker.start()
        self.broker.status.connect(lambda: updated())
        @pyqtSlot()
        def updated():
            self.cntMax = len(nm_in_db)
            self.cntNow = self.cntMax - 1
            self.btnRun.setEnabled(True)
        # App
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        # Labels
        self.label = QLabel('지난 당첨번호', self)
        self.label.move(20,10)
        self.label.setFixedWidth(400)
        self.draws = self.DrawLabels()
        self.balls = self.PredictLabels()
        # Buttons
        btn1 = QPushButton('<< 이전회차', self)
        btn2 = QPushButton('다음회차 >>', self)
        btn1.clicked.connect(self.do_action_btn1)
        btn2.clicked.connect(self.do_action_btn2)
        # btn.clicked.connect(lambda: do_action())
        # def do_action():
        btnBox = QHBoxLayout()
        btnBox.addWidget(btn1)
        btnBox.addWidget(btn2)
        self.btnRun = QPushButton('로또 번호 예측하기', self)
        self.btnRun.setFixedHeight(60)
        self.btnRun.setEnabled(False)
        self.btnRun.clicked.connect(self.do_action_btnRUN)
        self.do_prediction_signal.connect(self.broker.DoPrediction)
        self.broker.complete.connect(self.SetPredLabels)
        self.cBox = QCheckBox('학습 새롭게 하기 (예측에 2~3분 걸립니다.)')
        layout = QVBoxLayout()
        layout.addSpacing(10)
        layout.addWidget(self.label)
        layout.addSpacing(20)
        layout.addLayout(self.draws)
        layout.addSpacing(20)
        layout.addLayout(btnBox)
        layout.addSpacing(30)
        layout.addWidget(self.btnRun)
        layout.addWidget(self.cBox)
        layout.addSpacing(40)
        layout.addLayout(self.balls)
        layout.addStretch(10)
        self.setLayout(layout)
        self.show()
        #app.aboutToQuit.connect(self.closeEvent)

    def DrawLabels(self):
        self.label0 = QLabel('N', self)
        self.label1 = QLabel('U', self)
        self.label2 = QLabel('M', self)
        self.label3 = QLabel('B', self)
        self.label4 = QLabel('E', self)
        self.label5 = QLabel('R', self)
        for i in range(6):
            exec('self.label%s.setFixedSize(60,60)' % i)
            style = "border-radius: 30px; font-size: 14pt; qproperty-alignment: AlignCenter; "
            if i == 0:
                style += "background-color:gold;"
            elif i == 1:
                style += "background-color:dodgerblue;"
            elif i == 2:
                style += "background-color:lightcoral;"
            elif i == 3:
                style += "background-color:lightsteelblue;"
            elif i == 4:
                style += "background-color:limegreen;"
            else:
                style += "background-color:pink;"
            exec('self.label%s.setStyleSheet(style)' % i)
        hbox = QHBoxLayout()
        hbox.addWidget(self.label0)
        hbox.addWidget(self.label1)
        hbox.addWidget(self.label2)
        hbox.addWidget(self.label3)
        hbox.addWidget(self.label4)
        hbox.addWidget(self.label5)
        return hbox

    def SetLabels(self, nums):
        self.label0.setText(str(nums[0]))
        self.label1.setText(str(nums[1]))
        self.label2.setText(str(nums[2]))
        self.label3.setText(str(nums[3]))
        self.label4.setText(str(nums[4]))
        self.label5.setText(str(nums[5]))
        for i in range(6):
            exec('self.label%s.setFixedSize(60,60)' % i)
            style = "border-radius: 30px; font-size: 14pt; qproperty-alignment: AlignCenter; "
            if nums[i] <= 10:
                style += "background-color:gold;"
            elif nums[i] <= 20:
                style += "background-color:dodgerblue;"
            elif nums[i] <= 30:
                style += "background-color:lightcoral;"
            elif nums[i] <= 40:
                style += "background-color:lightsteelblue;"
            else:
                style += "background-color:limegreen;"
            exec('self.label%s.setStyleSheet(style)' % i)
  
    def PredictLabels(self):
        self.labelP0 = QLabel('L', self)
        self.labelP1 = QLabel('O', self)
        self.labelP2 = QLabel('T', self)
        self.labelP3 = QLabel('T', self)
        self.labelP4 = QLabel('O', self)
        self.labelP5 = QLabel('?', self)
        for i in range(6):
            exec('self.labelP%s.setFixedSize(60,60)' % i)
            style = "border-radius: 30px; font-size: 14pt; qproperty-alignment: AlignCenter; background-color:peachpuff;"
            exec('self.labelP%s.setStyleSheet(style)' % i)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.labelP0)
        hbox2.addWidget(self.labelP1)
        hbox2.addWidget(self.labelP2)
        hbox2.addWidget(self.labelP3)
        hbox2.addWidget(self.labelP4)
        hbox2.addWidget(self.labelP5)
        return hbox2

    @pyqtSlot(list)
    def SetPredLabels(self, nums):
        self.labelP0.setText(str(nums[0]))
        self.labelP1.setText(str(nums[1]))
        self.labelP2.setText(str(nums[2]))
        self.labelP3.setText(str(nums[3]))
        self.labelP4.setText(str(nums[4]))
        self.labelP5.setText(str(nums[5]))
        for i in range(6):
            exec('self.labelP%s.setFixedSize(60,60)' % i)
            style = "border-radius: 30px; font-size: 14pt; qproperty-alignment: AlignCenter; "
            if nums[i] <= 10:
                style += "background-color:gold;"
            elif nums[i] <= 20:
                style += "background-color:dodgerblue;"
            elif nums[i] <= 30:
                style += "background-color:lightcoral;"
            elif nums[i] <= 40:
                style += "background-color:lightsteelblue;"
            else:
                style += "background-color:limegreen;"
            exec('self.labelP%s.setStyleSheet(style)' % i)
        self.w.label.setText("예측이 완료되었습니다!!!")
        self.btnRun.setEnabled(True)
        # QMessageBox.information(self, "Information", "예측이 완료되었습니다!!!")

    def do_action_btn1(self):
        self.cntNow -= 1
        if self.cntNow < 0:
            self.cntNow = 0
        draw = nm_in_db[self.cntNow]['draw']
        date = nm_in_db[self.cntNow]['date']
        self.label.setText('제' + str(draw) +'회 당첨번호 (추첨일: ' + date + ')')
        self.SetLabels(nm_in_db[self.cntNow]['n'])

    def do_action_btn2(self):
        self.cntNow += 1
        if self.cntNow >= self.cntMax:
            self.cntNow = self.cntMax - 1
        draw = nm_in_db[self.cntNow]['draw']
        date = nm_in_db[self.cntNow]['date']
        self.label.setText('제' + str(draw) +'회 당첨번호 (추첨일: ' + date + ')')
        self.SetLabels(nm_in_db[self.cntNow]['n'])

    @pyqtSlot()
    def do_action_btnRUN(self):
        if self.w is None:
            self.w = AnotherWindow()
            self.w.show()
            sys.stdout = Stream(newText=self.onUpdateText)
            self.btnRun.setEnabled(False)
            self.btnRun.setText('진행현황 창 닫기')
            self.broker.mode = self.cBox.isChecked()
            self.do_prediction_signal.emit()
        else:
            self.w.close()
            self.w = None
            sys.stdout = sys.__stdout__
            # self.btnRun.setEnabled(False)
            # self.cBox.setEnabled(False)
            self.btnRun.setText('로또 번호 예측하기')
        # self.broker.mode = self.cBox.isChecked()
        # self.do_prediction_signal.emit()

    def onUpdateText(self, text):
        cursor = self.w.textbox.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.w.textbox.setTextCursor(cursor)
        self.w.textbox.ensureCursorVisible()

    def closeEvent(self, event):
        # reply = QMessageBox.question(self, 'Message', "Do you want to save?",
        #         QMessageBox.Yes, QMessageBox.No)
        if self.w:
            self.w.close()


class AnotherWindow(QWidget):
    """
    This "window" will show progess of the prediction.
    """
    def __init__(self):
        super().__init__()
        self.title = '진행현황 (Progress)'
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        layout = QVBoxLayout()
        self.label = QLabel("예측중입니다.")
        self.textbox = QPlainTextEdit(self)
        self.textbox.setFixedHeight(400)
        self.textbox.setStyleSheet("background-color:black;color:white;")
        layout.addSpacing(10)
        layout.addWidget(self.label)
        layout.addSpacing(10)
        layout.addWidget(self.textbox)
        layout.addSpacing(10)
        self.setLayout(layout)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(700, 100, 500, 500)
        self.textbox.setPlainText('progress')
        self.label.setStyleSheet("font-size: 12pt")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
