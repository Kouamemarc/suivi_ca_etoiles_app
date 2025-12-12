📊 Dashboard Closes Amiens & Beauvais
Analyse complète du CA, des commandes et des notes par marque

Ce projet propose une application Streamlit permettant de suivre, analyser et enrichir les données de closes des villes d’Amiens et Beauvais.
Il centralise le CA, le nombre de commandes, les performances horaires, ainsi que l’évolution des notes Uber Eats et Deliveroo pour chaque marque : Pepe Chicken, Out Fry, Starmash.

L’application inclut :

un dashboard d’analyse,

une page de saisie des données,

une page de gestion des objectifs,

un système d’alertes visuelles (🟢 🟡 🔴),

un export PDF professionnel,

et un fonctionnement optimisé pour mobile et multi-utilisateurs.

🚀 Fonctionnalités principales
🔹 1. Analyse du CA & des commandes

CA total, commandes totales, panier moyen

CA/h et commandes/h

Heatmap CA horaire

Courbes d’évolution du CA et des commandes selon la période de close

Top périodes de close

Objectifs automatiques appliqués :

Amiens → ≥ 350 € / close

Beauvais → ≥ 200 € / close

Indicateurs de performance :

🟢 OK

🟡 Moyen

🔴 Sous objectif

🔹 2. Analyse des notes (Uber Eats & Deliveroo)

Courbes d’évolution par marque et plateforme

Calcul des moyennes par marque

Comparatif global par ville

Objectif automatique :

Note minimale ≥ 4.5

Statut objectif par ligne (🟢 / 🔴)

🔹 3. Page Objectifs (modification en direct)

Une interface permet de modifier facilement :

l’objectif CA Amiens

l’objectif CA Beauvais

l’objectif de note Uber/Deliveroo

Les valeurs sont mémorisées dans la session Streamlit.

🔹 4. Saisie des données

Ajout intuitif de lignes dans :

CA_Close

Évolution_Notes

Les données mises à jour peuvent être téléchargées dans un Excel généré automatiquement.

🔹 5. Export PDF automatique

Génération d’un rapport PDF synthétique incluant :

objectifs

KPI CA

KPI commandes

KPI notes

filtres utilisés

Utilisable pour reporting interne, management, et audits de performance.

🔹 6. Optimisation mobile & multi-utilisateur

Layout centré

Graphiques responsives

Session indépendante pour chaque utilisateur

Déployable immédiatement sur Streamlit Cloud

🗂️ Structure du fichier de données

Le fichier suivi_close_amiens_beauvais.xlsx doit contenir 2 feuilles :

📄 Feuille CA_Close
Colonne	Description
Date	Date de la close
Ville	Amiens ou Beauvais
Nombre commandes	Total commandes
Chiffre d’affaires (€)	CA généré
Période de close	Ex : "23:00 - 00:00"

L’application calcule automatiquement :

durée horaire

CA horaire (€ / h)

commandes horaires

📄 Feuille Évolution_Notes
Colonne	Description
Date	Date
Ville	Amiens / Beauvais
Marque	Pepe / Out Fry / Starmash
Note Uber Eats	Valeur 0 à 5
Note Deliveroo	Valeur 0 à 5
🛠️ Installation locale

Cloner le projet :

git clone https://github.com/<user>/suivi_ca_etoiles_app.git
cd suivi_ca_etoiles_app


Installer les dépendances :

pip install -r requirements.txt


Lancer l'application :

streamlit run app.py

🌐 Déploiement Streamlit Cloud

Aller sur : https://streamlit.io/cloud

Se connecter avec GitHub

Créer une nouvelle app

Sélectionner ce repo

Fichier principal : app.py

Déployer 🚀

Chaque push GitHub redéploie automatiquement la version mise à jour.

📦 Technologies utilisées

Python 3

Streamlit

Pandas

Altair

ReportLab

Openpyxl

🛣️ Roadmap

 Passage à Google Sheets comme source de données centrale

 Persistance cloud des objectifs

 Page “Comparatif Amiens vs Beauvais”

 Export PDF avancé multi-pages

 Authentification utilisateurs (OAuth Google)

👨‍💻 Auteur

Marc Kouame
Dashboard, Data Automation & Food Delivery Analytics.

🤝 Contributions

Les PR sont les bienvenues.
Pour toute demande d'amélioration ou de nouvelles fonctionnalités, ouvrir une issue.
