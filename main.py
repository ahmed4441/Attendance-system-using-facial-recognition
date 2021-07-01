import face_recognition
#import face_landmark_detection
import cv2
import numpy as np
import os
from datetime import datetime
import pyttsx3
import time
import threading
import calendar
import sqlite3
from sqlite3 import Error
import base64

def frame_to_base64(frame):
    return base64.b64encode(frame)
def decoder(bb64):
    imgdata = base64.b64decode(bb64)
    filename = 'some_image.jpg'  # I assume you have a way of picking unique filenames
    with open(filename, 'wb') as f:
        f.write(imgdata)

attendanceesnames = []
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
lock = threading.Lock()


def welcome_guest(name):
    # print ("welcome")
    engine.say('Welcome ' + name)
    # time.sleep(2)
    engine.runAndWait()

# engine.say('The quick brown fox jumped over the lazy dog.')
# engine.runAndWait()

def sql_connection():
    try:
        con = sqlite3.connect('mydatabase.db')
        return con
    except Error:
        print(Error)


def sql_table(con):
    cursorObj = con.cursor()
    try:
        cursorObj.execute(
            "CREATE TABLE attendance(ID integer PRIMARY KEY, Name text, StudentID integer,TodayDate text, CurrentTime text, encodedIMGbase64 text)")
        con.commit()
    except:
        pass


def sql_insert(con, entities):
    cursorObj = con.cursor()
    cursorObj.execute(
        'INSERT INTO attendance(Name, StudentID, TodayDate, CurrentTime, encodedIMGbase64) VALUES(?, ?, ?, ?, ?)',
        entities)
    con.commit()


def sql_fetch(con, dy):
    # rows = [0]
    cursorObj = con.cursor()
    tuple1 = (dy,)
    cursorObj.execute("SELECT StudentID FROM attendance WHERE TodayDate = ?", tuple1)
    rows = cursorObj.fetchall()
    # print(rows[2][0])
    return rows


con = sql_connection()
sql_table(con)


class myThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        lock.acquire()
        welcome_guest(self.name)
        lock.release()
        # print ("Exiting " + self.name)


def print_time(threadName, counter, delay):
    while counter:
        # if exitFlag:
        # threadName.exit()
        time.sleep(delay)
        print("%s: %s" % (threadName, time.ctime(time.time())))
        counter -= 1

# Create new threads

# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

# Create arrays of known face encodings and their names

known_face_names = [

]
known_face_ids = [

]
known_face_encodings = []
# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
name = ""

# process_this_frame = True

pathlib = 'ImageAttendance'
images = []

myList = os.listdir(pathlib)
print(myList)
for cl in myList:
    currImg = cv2.imread(f'{pathlib}/{cl}')
    images.append(currImg)
    known_face_ids.append(os.path.splitext(cl)[0].split('-')[1])
    known_face_names.append(os.path.splitext(cl)[0].split('-')[0])
print(known_face_names)


def DbEncodings(images):
    known_face_encodings = []
    for image in images:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        enc = face_recognition.face_encodings(image)[0]
        known_face_encodings.append(enc)
    return known_face_encodings


def attendancedb(name, nameid, frame):
    noID = True
    dy = curr.strftime('%d-%m-%Y')
    idcheck = sql_fetch(con, dy)
    for i in range(len(idcheck)):
        if idcheck[i][0] != int(nameid):
            continue
        else:
            noID = False
            break
    if noID:
        _, jpeg_frame = cv2.imencode('.jpg', frame)
        # jpeg_frame = jpeg_frame[:, :, ::-1]
        b64 = frame_to_base64(jpeg_frame)
        decoder(b64)
        thread1 = myThread(1, name, 1)
        thread1.start()
        # print("thread started")
        dt = curr.strftime('%H:%M:%S')
        dy = curr.strftime('%d-%m-%Y')
        entities = (name, nameid, dy, dt, b64)
        sql_insert(con, entities)


encodeKnown = DbEncodings(images)
print('Encoding Complete')

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]
    # name = "unknown"

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations, num_jitters=44)

    for encodeFace in face_encodings:
        matchList = face_recognition.compare_faces(encodeKnown, encodeFace, tolerance=0.499)
        #print(matchList)
        if (np.argmax(matchList)):
            name = known_face_names[np.argmax(matchList)]
            nameid = known_face_ids[np.argmax(matchList)]
            attendancedb(name, nameid, rgb_small_frame)
        # print(matchList)
        # Display the results
        for (top, right, bottom, left) in face_locations:
            # print(f"Face found at: {face_locations}")
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            if not name:
                name = "unknown"
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            name = ""
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.circle(frame, (25, 15), 0, (0, 0, 255), 9)
    cv2.putText(frame, 'LIVE', (35, 30), font, 1.0, (0, 0, 255), 2)
    curr = datetime.now()
    dt = curr.strftime('%d-%m-%Y %H:%M:%S')
    cv2.putText(frame, dt, (380, 30), font, .7, (255, 0, 0), 1)
    # my_date = datetime.today()
    # day = calendar.day_name[my_date.weekday()]
    # cv2.putText(frame, day, (470, 60), font, .6, (255, 0, 0), 2)
    # Display the resulting image
    cv2.imshow('live feed', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
