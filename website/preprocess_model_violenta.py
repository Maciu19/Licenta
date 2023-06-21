import cv2
import numpy as np
from tensorflow.keras import models
from tensorflow.keras.applications.vgg19 import preprocess_input

class Detector:
   
    def __init__(self, filename):
        self.model = models.load_model('./website/model/hockey_10_epochs_925.h5')
        self.number_of_frames_model = 30
        self.img_dimensiune = 160
        self.filename = filename

    def get_frames(self):
        frames = np.zeros((self.number_of_frames_model, self.img_dimensiune, self.img_dimensiune, 3))

        rezultate = []

        cap = cv2.VideoCapture(self.filename)
        numar_total_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        times = int(numar_total_frame // self.number_of_frames_model)

        # Pentru fiecare 30 de frame (self.number_of_frames_model) aplic modelul 
        for c in range(times):
            for i in range(self.number_of_frames_model):

                ret, frame = cap.read()
                if ret == False:
                    return
                
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (self.img_dimensiune, self.img_dimensiune), interpolation=cv2.INTER_CUBIC)
                img = preprocess_input(img)
                img = img.astype(np.float32) / 255.0 

                frames[i][:] = img

                if i == self.number_of_frames_model - 1:
                    frames_predict = frames.reshape(-1, 30, 160, 160, 3)
                    rez = self.model.predict(frames_predict)
                    rezultate.append(rez[0])
                    
            frames = np.zeros((self.number_of_frames_model, self.img_dimensiune, self.img_dimensiune, 3))
        
        cap.release()
        return rezultate


    def writeVideo(self, rezultate):
        cap = cv2.VideoCapture(self.filename)
        out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (640, 480))
        numar_total_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        times = int(numar_total_frame // self.number_of_frames_model)

        for c in range(times):
            for i in range(self.number_of_frames_model):
                ret, frame = cap.read()
                if ret == False:
                    return
                
                frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_CUBIC)
                
                if rezultate[c][0] < rezultate[c][1]:
                    cv2.putText(frame, 'Neagresiv', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                else:
                    cv2.putText(frame, 'Agresiv', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                out.write(frame)
        
        cap.release()
        out.release()


def execute_model(path):
   detector = Detector(path)
   predictions = detector.get_frames()
   detector.writeVideo(predictions)