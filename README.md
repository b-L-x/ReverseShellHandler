<h1 align="center">🖥️ ReverseShellHandler</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python" />
  <img src="https://img.shields.io/badge/PyQt6-GUI-green?logo=qt" />
  <img src="https://img.shields.io/badge/build-pyinstaller-orange?logo=windows" />
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" />
</p>

<p align="center">
  <b>ReverseShellHandler</b> est une application GUI moderne en <b>Python (PyQt6)</b> permettant de gérer plusieurs <i>reverse shells</i> de manière centralisée et ergonomique.<br>
  Elle intègre un <b>terminal coloré</b> (compatible ANSI), la gestion multi-clients, des notifications sonores et une interface utilisateur claire.
</p>

---

<h2>✨ Fonctionnalités</h2>

<ul>
  <li>🔗 <b>Connexion multi-shells</b> : gérer plusieurs connexions simultanées.</li>
  <li>🎨 <b>Terminal amélioré</b> :
    <ul>
      <li>Couleurs ANSI (affichage clair des sorties).</li>
      <li>Protection du prompt (<code>$hell ></code>).</li>
      <li>Clic droit = <b>coller</b> directement dans le terminal.</li>
    </ul>
  </li>
  <li>🔔 <b>Notifications sonores</b> à la réception de nouvelles connexions (<code>notif.mp3</code>).</li>
  <li>🖼️ <b>Interface PyQt6</b> moderne, intuitive et robuste.</li>
  <li>🛡️ <b>Connexion robuste</b> : l’application ne plante plus en cas d’échec de connexion au serveur.</li>
  <li>📦 <b>Mode exécutable</b> : compilation facile en <code>.exe</code> avec icône personnalisée (<code>handler.ico</code>).</li>
</ul>

---

<h2>🖥️ Aperçu</h2>

<p><i>(captures d’écran à insérer ici si tu en as)</i></p>

---

<h2>🚀 Installation</h2>

<h3>Prérequis</h3>
<ul>
  <li><a href="https://www.python.org/downloads/">Python 3.10+</a></li>
  <li>Modules Python :
    <pre><code>pip install -r requirements.txt</code></pre>
  </li>
</ul>

<h3>Lancer l’application</h3>
<pre><code>python ReverseShellHandler.py</code></pre>

---

<h2>📦 Compilation en .exe</h2>

<p>Pour transformer le projet en exécutable Windows :</p>

<pre><code>pyinstaller --onefile --windowed ^
    --icon=handler.ico ^
    --add-data "notif.mp3;." ^
    ReverseShellHandler.py
</code></pre>

<p>L’exécutable sera disponible dans le dossier <b><code>dist/</code></b> :</p>

<pre><code>dist/ReverseShellHandler.exe
</code></pre>

<p>⚡ Tu peux aussi créer un script <code>build.bat</code> pour automatiser la compilation.</p>

---

<h2>🔊 Gestion des ressources</h2>

<p>L’application embarque ses ressources via PyInstaller :</p>

<pre><code class="language-python">import sys, os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

notif_sound = resource_path("notif.mp3")
</code></pre>

---

<h2>🛠️ Technologies utilisées</h2>
<ul>
  <li>🐍 Python 3.10+</li>
  <li>📦 PyQt6 (interface graphique)</li>
  <li>🎵 pygame (lecture audio)</li>
  <li>🛠️ PyInstaller (compilation en exécutable)</li>
</ul>

---

<h2>⚖️ Licence</h2>
<p>Ce projet est distribué sous licence <b>MIT</b> – libre d’utilisation et de modification.</p>

---

<h2>👨‍💻 Auteur</h2>
<ul>
  <li>Projet développé par <b>[Ton Nom/Pseudo]</b></li>
  <li>Contributions et améliorations bienvenues ! 🎉</li>
</ul>
