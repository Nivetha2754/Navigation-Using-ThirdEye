from compreface import CompreFace
from compreface.service import RecognitionService
from compreface.collections import FaceCollection
from compreface.collections.face_collections import Subjects

DOMAIN: str = 'http://192.168.1.239'
PORT: str = '8000'
API_KEY: str = 'dc8a7ab4-df5f-4e75-b7ac-aa04aa46d12c'

compre_face: CompreFace = CompreFace(DOMAIN, PORT)
recognition: RecognitionService = compre_face.init_face_recognition(API_KEY)
face_collection: FaceCollection = recognition.get_face_collection()
subjects: Subjects = recognition.get_subjects()

image_path: str = 'WhatsApp Image 2024-07-22 at 3.17.07 PM.jpeg'