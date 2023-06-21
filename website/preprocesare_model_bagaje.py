import tensorflow as tf
import numpy as np
import cv2

class Detector:

    def __init__(self, classesFilePath):
        with open(classesFilePath, 'r') as f:
            self.classes_list = f.read().splitlines()

        self.classes_list_interes = ['person', 'SUITCASE', 'HANDBAG', 'BACKPACK']
        self.classes_list_indexes = [1, 33, 31, 27]
        # clasele care ma intereseaza si indecsii lor din fisier-ul coco.names


    def load_model(self):
        self.model = tf.saved_model.load('./website/model/saved_model')

    def create_box(self, image, threshold=0.5):
        obiecte_detectate = {
            "person":[]
        }

        input_tensor = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_tensor = tf.convert_to_tensor(input_tensor)
        input_tensor = tf.expand_dims(input_tensor, axis = 0)

        detections = self.model(input_tensor)

        boxes = detections['detection_boxes'][0].numpy()
        class_indexes = detections['detection_classes'][0].numpy().astype(np.int32)
        class_scores = detections['detection_scores'][0].numpy()

        img_height, img_width, img_color_ch = image.shape

        index_boxes_filtered = tf.image.non_max_suppression(boxes, class_scores, max_output_size=50, iou_threshold=threshold, score_threshold=threshold)
        # non_max_suppression = selecteaza o singura entitate din mai multe entitati suprapuse

        if len(index_boxes_filtered) > 0:
            for i in index_boxes_filtered:
                box = tuple(boxes[i].tolist())
                class_confidence = round(100 * class_scores[i])
                class_index = class_indexes[i]

                if class_index in self.classes_list_indexes:
                    # Daca clasa pe care am gasit-o este in aria noastra de interes

                    class_text = self.classes_list[class_index].upper()
                    
                    y_min, x_min, y_max, x_max = box 

                    x_min, x_max = int(x_min * img_width), int(x_max * img_width)
                    y_min, y_max = int(y_min * img_height), int(y_max * img_height)
                    # Converteste coordonatele detectate ale imaginii procesate in coordonate reale ale imaginii.
                    # Aceasta este necesara pentru a desena dreptunghiurile de detectare. 
                    # x_min, x_max, y_min, y_max sunt proportionale cu dimensiunile imaginii de intrare

                    if class_index == 1:
                        # Daca am detectat o persoana
                        color = (255, 0, 0)

                        obiecte_detectate['person'].append([x_min, y_min, x_max, y_max])

                        cv2.putText(image, 'Persoana', (x_min, y_min - 10), cv2.FONT_HERSHEY_PLAIN, 1, color)  
                        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, thickness=1)
                    else:
                        # Daca am detectat un bagaj (nu o persoana), adaugam intr-un dicitionar coordonatele dreptunghiului care urmeaza sa fie pus
                        if not class_text in obiecte_detectate.keys():
                            obiecte_detectate[class_text] = []
                        obiecte_detectate[class_text].append([x_min, y_min, x_max, y_max])
                        
        distances_coordinates = []
        if len(obiecte_detectate['person']) > 0 and len(obiecte_detectate.keys()) > 1:
            # Daca avem persoane si bagaje desenam liniile
            nume_bagaje = list(obiecte_detectate.keys())
            nume_bagaje.remove('person')
            for lug in nume_bagaje:
                for i in obiecte_detectate['person']:
                    for j in obiecte_detectate[lug]:
                        # Calculam centrele dreptunghiurilor
                        persoana_centru = [int((i[0] + i[2]) / 2), int((i[1] + i[3]) / 2)]
                        bagaj_centru = [int((j[0] + j[2]) / 2), int((j[1] + j[3]) / 2)]

                        cv2.line(image, tuple(persoana_centru), tuple(bagaj_centru), (255, 255, 255), 1)   

                        d = np.linalg.norm(np.array(persoana_centru) - np.array(bagaj_centru))
                        # Calculam distanta dintre cele 2 puncte (centre)

                        cv2.rectangle(image, (j[0], j[1]), (j[2], j[3]), (0, 255, 0), thickness=1)

                        if lug == 'SUITCASE':
                            afisare_text = 'Valiza'
                        elif lug == 'HANDBAG':
                            afisare_text = 'Geanta'
                        elif lug == 'BACKPACK':
                            afisare_text = 'Rucsac'

                        cv2.putText(image, afisare_text, (j[0], j[1] - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))  


                        # Daca elementul a mai fost indentificat in trecut vom adauga noua distanta descoperita la acel obiect
                        # Daca elementul nu a mai fost indentificat cream un dictionar in lista

                        found = False

                        for k in distances_coordinates:
                            c = k['coordinates']
                            if c[0] == j[0] and c[1] == j[1] and c[2] == j[2] and c[3] == j[3]:
                               k['distance'].append(d)
                               found = True

                        if found == False:
                            distances_coordinates.append({
                                "distance" : [d],
                                "coordinates" : [j[0], j[1], j[2], j[3]]
                            })

            # Calculam minimul distantei pentru fiecare obiect identificat si il comparam cu o valoare prestabilita (200)
            # Daca distanta > valoare => Afisam textul "Abadonat" si un dreptunghi rosu 
            # Daca distanta < valoare => Afisam numele lui si un dreptunghi verde

            for x in distances_coordinates:
                m = min(x['distance'])
                if m > 200:
                    c = x['coordinates']
                    cv2.rectangle(image, (c[0], c[1]), (c[2], c[3]), (0, 0, 255), thickness=1)
                    cv2.putText(image, 'Abandonat', (c[0], c[1] - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), thickness=2)    
                                        
        # Daca nu avem persoane si avem doar bagaje, in acest caz vom pune obiectele ca fiind abandonate deoarece nu exista nici o persoana in jurul lor
        if len(obiecte_detectate.keys()) > 0 and len(obiecte_detectate['person']) == 0:
            for z in self.classes_list_interes:
                if z in obiecte_detectate:
                    for j in obiecte_detectate[z]:
                        cv2.rectangle(image, (j[0], j[1]), (j[2], j[3]), (0, 0, 255), thickness=1) 
                        cv2.putText(image, 'Abandonat', (j[0], j[1] - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), thickness=2) 

        return image
    
    def write_video(self, video_path, threshold=0.5):
        cap = cv2.VideoCapture(video_path)
        frame_number = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 15.0, (640, 640))

        i = 0

        ret, frame = cap.read()
        if ret == False:
            return 
        
        while ret:
            i += 1

            if i % 10 == 0:
                print(f'Frame {i} din {frame_number}')

            frame = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_CUBIC)
            box_frame = self.create_box(frame, threshold)

            out.write(box_frame)

            ret, frame = cap.read()

        cap.release()
        out.release()


def execute_model_bagaje(path):
    video_path = path
    threshold = 0.25

    detector = Detector('./website/model/coco.names')
    detector.load_model()
    detector.write_video(video_path, threshold)
