import cv2
import mediapipe as mp
import numpy as np
import time

from calculos import calculo_ear, calculo_mar

##### CONSTANTES #####
p_olho_esq = [385, 380, 387, 373, 362, 263] # já estão em sequência
p_olho_dir = [160, 144, 158, 153, 33, 133] # já estão em sequência
p_olhos = p_olho_esq + p_olho_dir
p_boca = [82, 87, 13, 14, 312, 317, 78, 308]

ear_limiar = 1.018 # Entre 1.000 e 1.010 no meu caso
mar_limiar = 0.1
##### /CONSTANTES #####

##### INICIALIZAÇÃO #####
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh


dormindo = 0 # Não está dormindo
contagem_piscadas = 0
t_piscadas = time.time()
c_tempo = 0 # Contador temporário de tempo
contagem_temporaria = 0 # Altera conforme a última quantidade de piscadas antes de ser dado um segundo
contagem_lista = []
##### /INICIALIZAÇÃO #####


##### INTERAÇÃO #####
with mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5, refine_landmarks=True) as facemesh:
    # (nível minímo de confiança para detectar uma face, mínimo de confiança para detectar os pontos da face)
    while cap.isOpened():
        tecla = cv2.waitKey(1)
        if tecla == 27: # Esc
            break

        sucesso, frame = cap.read()
        if not sucesso:
            print('Ignorando o frame vazio da camera')
            continue

        # 3ª var: FPS
        comprimento, largura, _ = frame.shape # para o _normalized_to_pixel_coordenates()

        # OpenCV por padrão entrega dados em BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        saida_facemesh = facemesh.process(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        try:
            # Itera sobre cada ponto da face coletado
            for face_landmarks in saida_facemesh.multi_face_landmarks:
                # Frame (fundo), pontos da face, drawing options
                mp_drawing.draw_landmarks(
                    frame, 
                    face_landmarks, 
                    mp_face_mesh.FACEMESH_CONTOURS,
                    # Blue, Green, Red (tonalidade tendendo pro Azul)
                    landmark_drawing_spec=mp_drawing.DrawingSpec(
                        color=(255,102,0),
                        thickness=1, 
                        circle_radius=1
                    ), 
                    # (tonalidade tendendo para o verde), espessura dos traços
                    connection_drawing_spec=mp_drawing.DrawingSpec(
                        color=(102,204,0), 
                        thickness=1,
                        circle_radius=1
                    )
                )

                face = face_landmarks.landmark
                for id_coord, coord_xyz in enumerate(face):
                    # Verifica se as coordenadas são de um ponto com id pertencente à lista referente aos olhos
                    if id_coord in p_olhos:
                        # Faz a conversão de coordenadas normalizadas para pixels
                        coord_cv = mp_drawing._normalized_to_pixel_coordinates(
                            coord_xyz.x, coord_xyz.y, largura, comprimento)
                        cv2.circle(frame, coord_cv, radius=2, color=(255,0,0), thickness=-1)

                    if id_coord in p_boca:
                        # Faz a conversão de coordenadas normalizadas para pixels
                        coord_cv = mp_drawing._normalized_to_pixel_coordinates(
                            coord_xyz.x, coord_xyz.y, largura, comprimento)
                        cv2.circle(frame, coord_cv, radius=2, color=(255,0,0), thickness=-1)
                        
                ear = calculo_ear(face, p_olho_dir, p_olho_esq)
                # Para ter um fundo e criar contraste para o texto
                # Ponto inicial | Ponto final do retângulo | cor (cinza) | thickness=-1 (retângulo preenchido)
                cv2.rectangle(
                    frame, pt1=(0,1), pt2=(290, 140), color=(58,58,55), thickness=-1)
                cv2.putText(
                    frame, 
                    text=f"EAR: {round(ear, 2)}", org=(1, 24),
                    fontFace=cv2.FONT_HERSHEY_DUPLEX,
                    fontScale=0.9, color=(255, 255, 255), thickness=2)
                
                mar = calculo_mar(face,p_boca)
                cv2.putText(
                    frame, 
                    f"MAR: {round(mar, 2)} {'Aberto' if mar>=mar_limiar else 'Fechado'}", 
                    (1, 50),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.9, (255, 255, 255), 2)
                
                if ear < ear_limiar and mar < mar_limiar: # Detecta a piscada
                    # dormindo já começa como 0, logo não haveria o problema da primeira inicialização de t_inicial quando dormindo = 1
                    t_inicial = time.time() if dormindo == 0 else t_inicial
                    # o if-ternário evita a contagem infinita quando se está dormindo)
                    contagem_piscadas = (contagem_piscadas + 1 if dormindo == 0 else contagem_piscadas)
                    dormindo = 1
                if (dormindo == 1 and ear >= ear_limiar) or mar >= mar_limiar:
                    # enquanto estiver com o olho fechado e o "ear" não for maior que o limiar (o olho ainda não abriu), não entra nesse caso para definir que o olho de fato abriu
                    # se a boca estiver aberta, significa que a pessoa está acordada
                    dormindo = 0 # Não se está mais em descanso

                t_final = time.time()
                tempo_decorrido = t_final - t_piscadas

                # Verifica se já se passou 1 segundo
                if tempo_decorrido >= c_tempo + 1:
                    c_tempo = tempo_decorrido # Atualiza o contador de segundos
                    piscadas_ps = contagem_piscadas - contagem_temporaria # Recebe as piscadas apenas do último intervalo de 1 segundo
                    contagem_temporaria = contagem_piscadas # Limite (inferior) passa a ser o Limite (superior) antigo
                    contagem_lista.append(piscadas_ps)
                    # Importante para não acessar índices inválidos enquanto a lista não tem 60 elementos. Após ela ultrapassar essa quantidade, conterá apenas os últimos 60 elementos
                    contagem_lista = contagem_lista if (len(contagem_lista) <= 60) else contagem_lista[-60:] # contagem_lista[-60:] -> Seleciona apenas os últimos 60 elementos
                
                # Somatório das piscadas do último minuto
                piscadas_pm = 15 if (tempo_decorrido <= 60) else sum(contagem_lista)
                # O if-ternário é para não prejudicar a análise enquanto ainda não completar 1 novo minuto

                # Só conta o tempo se o olho estiver fechado (dormindo verdadeiro)
                tempo = (t_final - t_inicial) if dormindo == 1 else 0.0


                cv2.putText(frame, f"Piscadas: {contagem_piscadas}", (1, 120),
                                                cv2.FONT_HERSHEY_DUPLEX,
                                                0.9, (109, 233, 219), 2)

                cv2.putText(
                    frame, 
                    text=f"Tempo: {round(tempo, 3)}", org=(1, 80),
                    fontFace=cv2.FONT_HERSHEY_DUPLEX,
                    fontScale=0.9, color=(255, 255, 255), thickness=2)
                
                if piscadas_pm < 10 or tempo>=1.5:
                    cv2.rectangle(frame, pt1=(30+340, 400+230), pt2=(610+340, 452+230), color=(109, 233, 219), thickness=-1) # Preenche todo o retângulo
                    # cv2.putText(
                    #     frame, 
                    #     text=f"Muito tempo com olhos fechados!", 
                    #     org=(80, 435), # cor do texto (mesmo cinza do retângulo)
                    #     fontFace=cv2.FONT_HERSHEY_DUPLEX,
                    #     fontScale=0.85, 
                    #     color=(58,58,55), 
                    #     thickness=1)

                    cv2.putText(frame, f"Pode ser que voce esteja com sono,", (400, 650),
                                        cv2.FONT_HERSHEY_DUPLEX, 
                                        0.85, (58,58,55), 1)
                    cv2.putText(frame, f"considere descansar.", (520, 680),
                                                            cv2.FONT_HERSHEY_DUPLEX, 
                                                            0.85, (58,58,55), 1)
                
        except Exception as e:
            # Caso ocorra algum erro, como por exemplo, a obstrução do rosto
            print(e)
            pass

        cv2.imshow('Camera', frame) # Não colocar acento no nome da imagem!
##### /INTERAÇÃO #####

cap.release()
cv2.destroyAllWindows()