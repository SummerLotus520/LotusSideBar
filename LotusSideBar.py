# coding:utf-8
import sys
import json
import os
import subprocess
import requests
import glob

from PyQt5.QtCore import Qt, QTimer, QDateTime,QEvent
from PyQt5.QtGui import QIcon, QPixmap,QFont
from PyQt5.QtWidgets import qApp,QApplication, QFrame, QVBoxLayout, QLabel, QMessageBox, QWidget, QHBoxLayout,QGridLayout
from qfluentwidgets import (Action, PrimaryPushButton, NavigationItemPosition, setTheme, Theme, FluentWindow,
                            SubtitleLabel, setFont, HyperlinkButton)
from qfluentwidgets import FluentIcon as FIF
def load_config():
    config_path = os.path.join(os.path.dirname(sys.executable), 'config.json')

    if not os.path.exists(config_path):
        default_config = {
            "theme": "AUTO",
            "custom_color": "AUTO",
            "date_time_font_size": 48,
            "quote_font_size": 32,
            "stationid": "rwUnO"
        }
        with open(config_path, 'w', encoding='utf-8') as file:
            json.dump(default_config, file, indent=4)
    with open(config_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def apply_config(config):
    theme = config.get("theme", "AUTO").upper()
    custom_color = config.get("custom_color", "AUTO")

    if theme == "LIGHT":
        setTheme(Theme.LIGHT)
    elif theme == "DARK":
        setTheme(Theme.DARK)
    else:
        setTheme(Theme.AUTO)
    
    # Apply custom color if not AUTO
    if custom_color != "AUTO":
        qApp.setStyleSheet(f"QWidget {{ background-color: {custom_color}; }}")

class DateTimeWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)  # 每秒更新一次
        self.update_date_time()

        # 设置样式
        config = load_config()
        font_size = config.get("date_time_font_size", 48)
        setFont(self, font_size)
        self.setAlignment(Qt.AlignCenter)

    def update_date_time(self):
        current_date = QDateTime.currentDateTime().toString('MM/dd ddd')
        current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
        self.setText(f"{current_date}\n{current_time}")

class DailyQuoteWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_quote)
        self.timer.start(1800000)  # 每半小时更新一次
        self.update_quote()

        # 设置样式
        config = load_config()
        font_size = config.get("quote_font_size", 32)
        setFont(self, font_size)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)  # 自动换行

    def update_quote(self):
        url = "https://v1.hitokoto.cn/?c=a&c=c&c=d&c=e&c=f&c=g&c=h&c=i&c=j&c=k&c=l&encode=text"
        response = requests.get(url)
        if response.status_code == 200:
            quote = response.text
            self.setText(quote)

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeInterface")

        self.dateTimeWidget = DateTimeWidget(self)
        self.weatherWidget = WeatherWidget(self)
        self.dailyQuoteWidget = DailyQuoteWidget(self)

        # 创建栅格布局
        grid = QGridLayout()
        grid.addWidget(self.dateTimeWidget, 0, 0, 1, 2, alignment=Qt.AlignTop | Qt.AlignHCenter)
        grid.addWidget(self.weatherWidget, 1, 0, 1, 2, alignment=Qt.AlignCenter)
        grid.addWidget(self.dailyQuoteWidget, 2, 0, 1, 2, alignment=Qt.AlignBottom | Qt.AlignHCenter)

        self.setLayout(grid)

class WeatherWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.update_weather()

        # 设置定时器，每半小时更新一次天气数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_weather)
        self.start_timer()

    def start_timer(self):
        current_time = QDateTime.currentDateTime()
        next_half_hour = current_time.addSecs(1800 - (current_time.time().minute() % 30) * 60 - current_time.time().second())
        interval = current_time.secsTo(next_half_hour) * 1000
        QTimer.singleShot(interval, self.start_half_hour_timer)

    def start_half_hour_timer(self):
        self.timer.start(1800000)  # 每半小时更新一次

    def update_weather(self):
        config = self.load_config()
        weather_data = self.fetch_weather_data(config["stationid"])
        if weather_data:
            self.display_weather(weather_data)

    def load_config(self):
        # 假设配置文件是一个JSON文件
        with open('config.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    def fetch_weather_data(self, stationid):
        url = f"http://www.nmc.cn/rest/weather?stationid={stationid}"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            self.save_weather_data(weather_data, stationid)
            return weather_data
        return None

    def save_weather_data(self, weather_data, stationid):
        now = QDateTime.currentDateTime().toString('yyyyMMdd-HHmmss')
        folder_path = os.path.join(os.path.dirname(sys.executable), 'WeatherJson')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, f"{now}-{stationid}.json")
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(weather_data, file, indent=4, ensure_ascii=False)

    def get_previous_weather_data(self, key):
        folder_path = os.path.join(os.path.dirname(sys.executable), 'WeatherJson')
        files = sorted(glob.glob(os.path.join(folder_path, '*.json')), reverse=True)
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                value = self.extract_value(data, key)
                if value != "9999":
                    return value
        return "Err"

    def extract_value(self, data, key):
        real = data["data"]["real"]
        weather = real["weather"]
        wind = real["wind"]
        if key in weather:
            return weather[key]
        elif key in wind:
            return wind[key]
        return "Err"

    def display_weather(self, weather_data):
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)

        # 清空布局
        for i in reversed(range(self.layout.count())): 
            widget = self.layout.itemAt(i).widget()
            if widget is not None: 
                widget.deleteLater()

        real = weather_data["data"]["real"]
        station = real["station"]
        weather = real["weather"]
        wind = real["wind"]
        air = weather_data["data"]["air"]

        # 处理9999的情况
        def get_valid_data(current, key):
            value = current if current != "9999" else self.get_previous_weather_data(key)
            return value if value != "9999" else "Err"

        # 获取所有需要显示的数据
        city = station['city']
        temperature = weather['temperature']
        humidity = weather['humidity']
        wind_direct = get_valid_data(wind['direct'], 'direct')
        wind_power = get_valid_data(wind['power'], 'power')
        air_quality = air['text']
        rain = weather['rain']
        feelst = weather['feelst']

        # 第一行：城市、温度、湿度、风速风向
        city_label = QLabel(f"{city} {temperature}°C 湿度: {humidity}% 风速风向: {wind_direct} {wind_power}")
        setFont(city_label, 24)
        city_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(city_label)

        # 第二行：空气质量、降水量、体感温度
        air_label = QLabel(f"空气质量: {air_quality} 降水量: {rain}mm 体感温度: {feelst}°C")
        setFont(air_label, 24)
        air_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(air_label)

        # 第三行：预警信息（如果有）
        if "warn" in real and real["warn"]["alert"] != "9999":
            warn = real["warn"]
            alert_text = warn["alert"].split("信号")[0] + "信号"
            warn_label = QLabel(alert_text)
            setFont(warn_label, 24)
            warn_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(warn_label)

        # 七日天气预报
        tempchart = weather_data["data"]["tempchart"]
        today = QDateTime.currentDateTime().toString('yyyy/MM/dd')
        start_index = next((index for (index, d) in enumerate(tempchart) if d["time"] == today), None)
        
        if start_index is not None:
            # 尝试获取七天的数据
            for days in range(7, 0, -1):
                end_index = start_index + days
                if end_index <= len(tempchart):
                    for i in range(start_index, end_index):
                        day_data = tempchart[i]
                        day_of_week = "今天" if i == start_index else QDateTime.fromString(day_data["time"], 'yyyy/MM/dd').toString('ddd')
                        
                        # 处理9999的情况
                        max_temp = day_data['max_temp'] if day_data['max_temp'] != "9999" else "Err"
                        min_temp = day_data['min_temp'] if day_data['min_temp'] != "9999" else "Err"
                        day_text = day_data['day_text'] if day_data['day_text'] != "9999" else "Err"
                        night_text = day_data['night_text'] if day_data['night_text'] != "9999" else "Err"
                        
                        forecast_label = QLabel(f"{day_of_week} {max_temp}°C/{min_temp}°C {day_text}/{night_text}")
                        setFont(forecast_label, 35)
                        forecast_label.setAlignment(Qt.AlignCenter)
                        
                        self.layout.addWidget(forecast_label)
                    break
            else:
                # 如果无法获取到足够的数据，将七天的数据项全部生成，并将数值全部填写成Err
                for i in range(7):
                    day_of_week = QDateTime.currentDateTime().addDays(i).toString('ddd')
                    forecast_label = QLabel(f"{day_of_week} Err°C/Err°C Err/Err")
                    setFont(forecast_label, 35)
                    forecast_label.setAlignment(Qt.AlignCenter)
                    self.layout.addWidget(forecast_label)
        else:
            # 如果没有找到当天的数据，将七天的数据项全部生成，并将数值全部填写成Err
            for i in range(7):
                day_of_week = QDateTime.currentDateTime().addDays(i).toString('ddd')
                forecast_label = QLabel(f"{day_of_week} Err°C/Err°C Err/Err")
                setFont(forecast_label, 35)
                forecast_label.setAlignment(Qt.AlignCenter)
                self.layout.addWidget(forecast_label)

def setFont(label, size):
    font = label.font()
    font.setPointSize(size)
    label.setFont(font)


class SettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingInterface")
        self.layout = QVBoxLayout(self)

        # Add Lotus.png
        pixmap = QPixmap('Lotus.png')
        imageLabel = QLabel(self)
        imageLabel.setPixmap(pixmap)
        imageLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(imageLabel, 1, Qt.AlignCenter)

        # Add text labels
        titleLabel = SubtitleLabel('LotusSideBar', self)
        titleLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(titleLabel, 1, Qt.AlignCenter)

        authorLabel = SubtitleLabel('作者：Lotus', self)
        authorLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(authorLabel, 1, Qt.AlignCenter)

        # Add GitHub hyperlink button
        githubButton = HyperlinkButton(
            url='https://github.com/SummerLotus520/LotusSideBar',
            text='Github',
            parent=self,
            icon=FIF.GITHUB
        )
        self.layout.addWidget(githubButton, 1, Qt.AlignCenter)

        # Add config button
        configButton = PrimaryPushButton('Open config.json', self)
        configButton.clicked.connect(self.openConfig)
        self.layout.addWidget(configButton, 1, Qt.AlignCenter)

        # Add reload button
        reloadButton = PrimaryPushButton('Reload', self)
        reloadButton.clicked.connect(self.reloadApp)
        self.layout.addWidget(reloadButton, 1, Qt.AlignCenter)

        # Add exit button
        exitButton = PrimaryPushButton('Exit', self)
        exitButton.clicked.connect(self.exitApp)
        self.layout.addWidget(exitButton, 1, Qt.AlignCenter)

    def openConfig(self):
        if not os.path.exists(CONFIG_PATH):
            QMessageBox.warning(self, 'Error', 'config.json not found!')
            return

    # 检查 VS Code 和 Notepad 的路径
        if os.path.exists('C:/Program Files/Microsoft VS Code/Code.exe'):
            editor = 'C:/Program Files/Microsoft VS Code/Code.exe'
        elif os.path.exists('C:/Program Files (x86)/Microsoft VS Code/Code.exe'):
            editor = 'C:/Program Files (x86)/Microsoft VS Code/Code.exe'
        else:
            editor = 'notepad'

        subprocess.call([editor, CONFIG_PATH])


    def reloadApp(self):
        config = load_config()
        apply_config(config)
        QMessageBox.information(self, 'Reload', 'Configuration reloaded successfully!')

    def exitApp(self):
        QApplication.instance().quit()

class Window(FluentWindow):
    def __init__(self):
        super().__init__()

        # create sub interface
        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.resize(int(1920 * 0.3), 1080)  # 设置窗口宽度为屏幕的30%，高度为全屏高度
        self.setWindowIcon(QIcon('Lotus.png'))
        self.setWindowTitle('LotusSideBar')  # 设置窗口标题

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w - self.width(), -50)  # 固定窗口位置 
        self.setWindowFlags(Qt.WindowStaysOnBottomHint)

    def enterEvent(self, event):
        self.setWindowOpacity(0.3)  # 鼠标进入时设置透明度为30%
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setWindowOpacity(1.0)  # 鼠标离开时恢复透明度
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.setWindowOpacity(0.3)  # 鼠标点击时设置透明度为30%
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setWindowOpacity(1.0)  # 鼠标释放时恢复透明度
        super().mouseReleaseEvent(event)

if __name__ == '__main__':

    app = QApplication(sys.argv)

    # 设置全局字体为 MiSans
    font = QFont("MiSans")
    font.setWeight(QFont.Normal)
    app.setFont(font)

    config = load_config()
    apply_config(config)

    w = Window()
    w.show()
    app.exec_()
