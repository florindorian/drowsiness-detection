import cv2


cap = cv2.VideoCapture(0)
RESOLUCAO_X = 1280
RESOLUCAO_Y = 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCAO_X)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCAO_Y)

while cap.isOpened(): # ou: while True:
    sucesso, frame = cap.read()

    tecla = cv2.waitKey(1)
    if tecla == 27: # Esc
        break

    if not sucesso:
        print('Ignorando o frame vazio da camera')
        continue

    cv2.imshow('Camera', frame) # Não colocar acento no nome da imagem!

cap.release()
cv2.destroyAllWindows()