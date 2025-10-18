import os
import cv2
import base64
import numpy as np
import time
from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import FaceData
from .serializers import FaceDataSerializer

# Haar cascade for face detection
haar_file = os.path.join(settings.BASE_DIR, "ai", "haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(haar_file)

# LBPH recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
label_map = {}  # label -> username mapping

def train_recognizer():
    """
    Train LBPH recognizer on current dataset.
    """
    global label_map
    faces_list = []
    labels_list = []
    label_map = {}
    label_counter = 0
    faces_root = os.path.join(settings.MEDIA_ROOT, "faces")

    if not os.path.exists(faces_root):
        return

    for username in os.listdir(faces_root):
        user_folder = os.path.join(faces_root, username)
        if os.path.isdir(user_folder):
            label_map[label_counter] = username
            for img_file in os.listdir(user_folder):
                img_path = os.path.join(user_folder, img_file)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    faces_list.append(img)
                    labels_list.append(label_counter)
            label_counter += 1

    if faces_list:
        recognizer.train(faces_list, np.array(labels_list))
    else:
        # Clear recognizer if no data
        recognizer.clear()

# Train recognizer on server start
train_recognizer()


class FaceDataViewSet(viewsets.ModelViewSet):
    queryset = FaceData.objects.all().order_by('-id')
    serializer_class = FaceDataSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    @csrf_exempt
    @action(detail=False, methods=['post'])
    @permission_classes([AllowAny])
    def upload_face(self, request):
        username = request.data.get("username")
        img_data = request.data.get("image")
        if not username or not img_data:
            return Response({"error": "username and image required"}, status=400)

        try:
            if ";base64," not in img_data:
                return Response({"error": "Invalid image format"}, status=400)

            img_str = img_data.split(";base64,")[-1]
            np_img = np.frombuffer(base64.b64decode(img_str), np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if img is None:
                return Response({"error": "Failed to decode image"}, status=400)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 4)
            if len(faces) == 0:
                return Response({"error": "No face detected"}, status=400)

            (x, y, w, h) = faces[0]
            face_crop = cv2.resize(gray[y:y+h, x:x+w], (130, 100))

            user_folder = os.path.join(settings.MEDIA_ROOT, "faces", username)
            os.makedirs(user_folder, exist_ok=True)

            timestamp = int(time.time() * 1000)
            filename = f"{username}_{timestamp}.png"
            file_path = os.path.join(user_folder, filename)

            success = cv2.imwrite(file_path, face_crop)
            if not success:
                return Response({"error": "Failed to save image"}, status=500)

            record = FaceData.objects.create(username=username, image=f"faces/{username}/{filename}")
            serializer = FaceDataSerializer(record, context={'request': request})

            # Retrain recognizer after new face upload
            train_recognizer()

            return Response({"message": f"✅ Face saved for {username}", "face": serializer.data}, status=200)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)


class DetectFaceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        img_data = request.data.get("image")
        if not img_data or ";base64," not in img_data:
            return Response({"error": "Invalid image"}, status=400)

        try:
            img_bytes = base64.b64decode(img_data.split(";base64,")[-1])
            img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                return Response({"error": "Cannot decode image"}, status=400)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces_detected = face_cascade.detectMultiScale(gray, 1.3, 4)
            for (x, y, w, h) in faces_detected:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0,255,0), 3)

            _, buf = cv2.imencode('.jpg', img)
            return Response({
                "faces_detected": len(faces_detected),
                "image": f"data:image/jpeg;base64,{base64.b64encode(buf).decode()}"
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class RecognizeFaceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        img_data = request.data.get("image")
        if not img_data or ";base64," not in img_data:
            return Response({"error": "Invalid image"}, status=400)

        try:
            img_bytes = base64.b64decode(img_data.split(";base64,")[-1])
            frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces_info = []
            faces_detected = face_cascade.detectMultiScale(gray_frame, 1.3, 4)

            for (x, y, w, h) in faces_detected:
                face_crop = cv2.resize(gray_frame[y:y+h, x:x+w], (130, 100))
                if len(label_map) > 0:
                    label, confidence = recognizer.predict(face_crop)
                    username = label_map.get(label, "Unknown")
                else:
                    username = "Unknown"

                faces_info.append({"x": x, "y": y, "w": w, "h": h, "username": username})
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, username, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

            _, buf = cv2.imencode('.jpg', frame)
            img_base64 = base64.b64encode(buf).decode()
            return Response({"faces_info": faces_info, "image": f"data:image/jpeg;base64,{img_base64}"})

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class ResetRecognizerView(APIView):
    """
    Endpoint to reset and retrain recognizer (after deleting dataset manually).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        train_recognizer()
        return Response({"message": "✅ Recognizer reset and retrained"})
