import numpy as np

def calculo_ear(face, p_olho_dir, p_olho_esq):
    # Para evitar problemas como divisão por 0
    try: 
        face = np.array([[coord.x, coord.y] for coord in face]) # cria uma lista com apenas 2 das dimensões coletadas pelo mediapipe
        # Coleta apenas os parâmetros de face do olho esquerdo e direito
        face_esq = face[p_olho_esq,:]
        face_dir = face[p_olho_dir,:]

        # np.linalg.norm: Calcula a distância euclidiana | os pontos já estão na ordem, mas deveria ser: (||p2 - p6|| + ||p3 - p5||)/(2 * ||p1 - p4||)
        ear_esq = (np.linalg.norm(face_esq[0] - face_esq[1]) + np.linalg.norm(face_esq[2] - face_esq[3])) / (2 * np.linalg.norm(face_esq[0] - face_esq[1]))
        ear_dir = (np.linalg.norm(face_dir[0] - face_dir[1]) + np.linalg.norm(face_dir[2] - face_dir[3])) / (2 * np.linalg.norm(face_dir[0] - face_dir[1]))
    except Exception as e:
        print(e)
        ear_esq = 0
        ear_dir = 0
    
    media_ear = (ear_esq + ear_dir)/2
    return media_ear


def calculo_mar(face,p_boca):
    # Ao abrir a boca ou sorrir, o MAR aumenta
    try:
        face = np.array([[coord.x, coord.y] for coord in face])
        face_boca = face[p_boca,:]

        mar = (np.linalg.norm(face_boca[0]-face_boca[1])+np.linalg.norm(face_boca[2]-face_boca[3])+np.linalg.norm(face_boca[4]-face_boca[5]))/(2*(np.linalg.norm(face_boca[6]-face_boca[7])))
    except:
        mar = 0.0

    return mar