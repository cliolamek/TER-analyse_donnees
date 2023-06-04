import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import statistics

##### IMPORTATION DES DONNÉES #####

GF = abs(pd.read_csv('C:/Users/clio1/Desktop/M1 SC COG/TER AAGRIP/Expé/données/maintien1.csv'))[:30000]
GF2 = abs(pd.read_csv('C:/Users/clio1/Desktop/M1 SC COG/TER AAGRIP/Expé/données/maintien2.csv'))
GFc = abs(pd.read_csv('C:/Users/clio1/Desktop/M1 SC COG/TER AAGRIP/Expé/données/chute1.csv'))
GFc2 = abs(pd.read_csv('C:/Users/clio1/Desktop/M1 SC COG/TER AAGRIP/Expé/données/chute2.csv'))
marker = abs(pd.read_csv('C:/Users/clio1/Desktop/M1 SC COG/TER AAGRIP/Expé/données/markers.csv', usecols=['Time (s)', 'Fz (N)', 'AI7 (V)']))

#GF, GF2 : maitien continu de la cellule ; GFc, GFc2 : maintien puis chute de la cellule ; marker : cellule déposée sur la table + triggers


#Identification des fréquences d'échantillonnage

donnees = [('GF', GF), ('GF2', GF2), ('GFc', GFc), ('GFc2', GFc2), ('marker', marker)]

for nom, i in donnees:
    diff_temps = i['Time (s)'].diff()  # Calcul de la différence de temps entre les échantillons
    fe = 1 / diff_temps.mean()  # Calcul de la fréquence d'échantillonnage (inverse de la moyenne des différences)
    print(f"Fréquence d'échantillonnage de {nom} : {fe} Hz")




##### PRÉ-TRAITEMENT (pour GF et marker UNIQUEMENT) ######

# Retrait des valeurs manquantes de grip_force
GF = GF.dropna()
marker = marker.dropna()

# Rééchantillonnage (de 500 Hz à 200 Hz)
exemple = [('GF', GF), ('marker', marker)]

for nom, df in exemple:
    df['Time (s)'] = pd.to_datetime(df['Time (s)'], unit='s')
    df = df.set_index('Time (s)')
    nv_df = df.resample('5ms').mean() # On prend une mesure toutes les 5 millisecondes (200 Hz)
    grip_force = nv_df['Fz (N)']
#Création de nouveaux data frames 'GF_rs' et 'marker_rs', et leurs valeurs de grip force 'grip_force_GF' et 'grip_force_marker'
    nv_nom = f"{nom}_rs"
    nv_gf = f"grip_force_{nom}"
    globals()[nv_nom] = nv_df
    globals()[nv_gf] = grip_force


# Moyennes pour la baseline
gf_rs = [('GF', grip_force_GF), ('marker', grip_force_marker)]

for nom, i in gf_rs:
    moy = f"moyenne_{nom}"
    moyenne = statistics.mean(i[:41]) # On prend les 41 premières valeurs de grip force (jusqu'à 200 ms)
    globals()[moy] = moyenne


# Normalisation des valeurs en prenant les valeur de référence (moyenne_GF et moyenne_marker)
GF_normal = pd.DataFrame()
GF_normal['temps'] = GF_rs.index
GF_rs.reset_index(drop=True, inplace=True)
GF_normal['grip_force'] = GF_rs['Fz (N)'] - moyenne_GF

marker_normal = pd.DataFrame()
marker_normal['temps'] = marker_rs.index
marker_rs.reset_index(drop=True, inplace=True)
marker_normal['grip_force'] = marker_rs['Fz (N)'] - moyenne_marker


##### PLOT TEST #####
plt.figure()
x = np.linspace(0.0, 60.0, 12000)
plt.plot(x, GF_normal['grip_force'][:12000]) # Prendre les 12000 premières valeurs (= 60 secondes)
plt.plot(x, marker_normal['grip_force'][:12000])
plt.xlabel('Temps (s)')
plt.ylabel('Grip force (N)')
plt.title(f'Données de grip force, baseline à {moyenne_GF} N')
plt.ylim(-1, 1)
plt.show()


##### PLOT APRÈS EXCLUSION DE DONNÉES (À TITRE DE DÉMONSTRATION) #####
# Suppression des lignes de GF où les valeurs de grip force ont des variations de 0.2 N ou plus par rapport à la baseline
GF_var = GF_normal.drop(GF_normal[GF_normal['grip_force'] > 0.2].index)

# Suppression des lignes de GF où les valeurs successives ont un écart de 0.1 N ou plus en l'espace de 0.1 secondes
GF_var_2 = GF_var.set_index('temps')
window = GF_var_2['grip_force'].rolling(window=int(0.1 * 200)) # 0.1 pour la fenêtre (en secondes), et 200 pour la fréquence d'échantillonnage
GF_final = GF_var_2[window.max() - window.min() <= 0.1 * 200]


plt.figure()
x = np.linspace(0.0, 10.0, 2000)
plt.plot(x, GF_var['grip_force'][:2000], alpha=0.5, label= 'Après retrait des valeurs > 0.2 N') # Prendre les 2000 premières valeurs (= 10 secondes)
plt.plot(x, GF_final['grip_force'][:2000], color="red", alpha=0.5, label= "Après retrait des valeurs dont l'écart > 0.1 N sur 0.1 s" )
plt.xlabel('Temps (s)')
plt.ylabel('Grip force (N)')
plt.title("Données de grip force après application des critères d'exclusion \n (à titre de démonstration)")
plt.ylim(-0.2, 0.25)
plt.legend()
plt.show()


##### FILTRAGE #####

# Butterworth passe-bas
order = 4
cutoff_freq = 15
b, a = signal.butter(order, cutoff_freq, fs=500, btype='low')


# Appliquer le filtre Butterworth aux valeurs de grip force
donnees_filtre = [('marker', marker_normal['grip_force']), ('GF', GF_normal['grip_force'])]

for nom, i in donnees_filtre:
    gff = f"GF_filtre_{nom}"
    grip_force_filtre = signal.filtfilt(b, a, i)
    globals()[gff] = grip_force_filtre



##### DONNÉES PERTINENTES #####

# Moyenne des valeurs de grip force pour GF
meanGF = statistics.mean(grip_force_GF)
print(f"La moyenne de grip force pour les données de maintien en continu est de {meanGF}")

# Création d'un data frame avec la moyenne pour le mettre dans le plot
meanGF_df = GF_normal
meanGF_df['grip_force'] = meanGF-moyenne_GF

# Maximum d'écart à la baseline pour GF
maxGF = GF_filtre_GF.max()
print(f"Le maximum d'écart à la baseline pour les données de maintien en continu est de {maxGF}")


##### PLOT FINAL #####

plt.figure()
x = np.linspace(0.0, 60.0, 12000)
plt.plot(x, GF_filtre_GF[:12000], label="Données de maintien en continu")
plt.plot(x, GF_filtre_marker[:12000], label="Données de la cellule posée sur la table")
plt.plot(x, marker_rs['AI7 (V)'][24000:36000]-1, color='black', alpha=0.2) #Pour afficher les triggers. Etant donné qu'ils apparaissaient au-delà de notre fenêtre, je les ai décalés pour qu'ils soient visibles
plt.plot(x, meanGF_df['grip_force'], color='red', label="Moyenne de force de maitien en continu")
plt.xlabel('Temps (s)')
plt.ylabel('Grip force (N)')
plt.title(f'Données de grip force (filtrées), baseline à {moyenne_GF} N')
plt.ylim(-1, 1)
plt.legend()
plt.show()





