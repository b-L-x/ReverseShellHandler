<!-- Reverse Shell Handler Pro — README section (HTML-friendly for GitHub) -->
<h1 align="center">Reverse Shell Handler Pro</h1>

<p align="center">
  <em>Client GUI PyQt6 pour recevoir, visualiser et piloter des shells à distance, avec terminal ANSI, génération de payloads, Whois en masse, proxy et alertes.</em>
</p>
![Screenshot](https://i.ibb.co/LhcFXX8s/02.png)
![Employee data](https://i.ibb.co/LhcFXX8s/02.png "Employee Data title")
<img src="[http://url/image.png](https://i.ibb.co/LhcFXX8s/02.png)" >

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue"/>
  <img alt="PyQt6" src="https://img.shields.io/badge/GUI-PyQt6-41b883"/>
  <img alt="Status" src="https://img.shields.io/badge/Build-Client--only-informational"/>
</p>

<hr/>

<h2>✨ Points forts</h2>
<ul>
  <li><strong>Interface moderne PyQt6</strong> avec panneau latéral animable, tableau de bord et pile d’onglets de terminaux par session (<code>QSplitter</code>, <code>QStackedWidget</code>). <!-- UI layout -->
  </li>
  <li><strong>Terminal type PuTTY</strong> :
    <ul>
      <li>Invite protégée (<code>$hell &gt;</code>), blocage des edits avant l’invite, coller au clic droit.</li>
      <li>Rendu <strong>ANSI 16/256 couleurs</strong>, gras/italique, inverse, et couleurs xterm étendues (38/48 ; 24-bit mappé). <!-- ANSI rendering -->
      </li>
      <li>Nettoyage CR/LF et insertion automatique de fin de ligne.</li>
    </ul>
  </li>
  <li><strong>Gestion multi-shells</strong> : liste des connexions actives, terminal dédié par shell, changement instantané, fermeture propre à la déconnexion. Requête initiale des shells actifs au serveur à la connexion.</li>
  <li><strong>Reconnexion automatique</strong> avec timer, journal d’événements horodaté et zone d’alerte.</li>
  <li><strong>Proxy intégré (PySocks)</strong> : SOCKS5/SOCKS4/HTTP, avec authentification optionnelle, timeouts adaptés. Activation/désactivation depuis l’UI, persistance en conf.</li>
  <li><strong>Alertes MP3 (pygame)</strong> : lecture d’un fichier MP3 au nouvel événement (activable/désactivable, sélection de fichier dans l’UI).</li>
  <li><strong>Whois</strong> :
    <ul>
      <li>Whois pour une IP active (fenêtre dédiée détaillant ASN, registry, nets, données brutes).</li>
      <li><strong>Whois en masse</strong> sur toutes les IPs uniques actives via thread dédié ; affichage tabulaire (IP, code pays, CIDR ASN, registry, description), avec copie en un clic.</li>
    </ul>
  </li>
  <li><strong>Générateur de payloads</strong> :
    <ul>
      <li>Plateformes : Windows, Linux, macOS, Android, PHP, Python, Bash.</li>
      <li>Types : Reverse/Bind shell, Meterpreter, Web shell, Empire (PS).</li>
      <li>Encodages : None, Base64, Hex, URL, <code>powershell -enc</code> (UTF-16LE conforme pour PS).</li>
      <li>Prévisualisation brève + fenêtre <em>View Full Payload</em> pour le code complet.</li>
    </ul>
  </li>
  <li><strong>Préférences persistantes</strong> : hôte/port, auto-connect, proxy, fichier MP3, etc. (fichier <code>ReverseShellHandler.conf</code>).</li>
</ul>

<hr/>

<h2>🧱 Architecture &amp; composants</h2>
<ul>
  <li><code>ReverseShellClient</code> (QMainWindow) : gestion socket, file de messages, signaux (nouveau shell, sortie, déconnexion, statut), UI et persistance.</li>
  <li><code>TerminalWidget</code> : <code>QTextEdit</code> stylé monospace + parseur ANSI maison (SGR, 8/16/256 couleurs), invite protégée, entrée commande via signal.</li>
  <li><code>PayloadGeneratorWidget</code> : formulaires (plateforme, arch, type, encodage, extension, nom), génération de snippets (msfvenom simplifiés, PS/Bash).</li>
  <li><code>BulkWhoisThread</code> + fenêtres Whois : requêtes IPWhois en thread, table résultats extensible (copie presse-papiers, drapeaux si disponibles).</li>
  <li>Options Proxy/MP3 : groupes dédiés, champs validés et désactivés si lib absente.</li>
</ul>

<hr/>

<h2>⚙️ Dépendances optionnelles</h2>
<ul>
  <li><strong>PySocks</strong> (proxy) — l’UI du proxy est désactivée si non présent.</li>
  <li><strong>pygame</strong> (alertes MP3) — alertes désactivées si non présent.</li>
  <li><strong>ipwhois</strong> (Whois) — fonctionnalités Whois désactivées si absent.</li>
  <li><strong>requests</strong> (drapeaux pays dans la table Whois) — facultatif.</li>
</ul>

<hr/>

<h2>🚀 Lancer l’application</h2>
<pre><code>python ReverseShellHandler.py [server_host] [server_port]
# Ex. : python ReverseShellHandler.py 127.0.0.1 5555
</code></pre>
<p>
À la première connexion, l’UI sauvegarde vos paramètres (auto-connect activé) ; un timer prend le relais en cas de coupure (reconnexion cyclique).
</p>

<hr/>

<h2>🖥️ Terminal &amp; commandes</h2>
<ul>
  <li>Chaque shell ouvre un terminal dédié ; la sortie est routée et rendue avec couleur.</li>
  <li>Des jeux de <em>commandes prédéfinies</em> par OS sont fournis (réseau/système), et l’envoi de commandes custom est proposé via une boîte de dialogue.</li>
</ul>

<hr/>

<h2>🔐 Avertissement légal</h2>
<p>
Ce projet est fourni <strong>strictement pour des tests en environnement contrôlé</strong> et pour l’apprentissage. L’auteur et les contributeurs déclinent toute responsabilité en cas d’usage illégal ou non autorisé. Assurez-vous de disposer de l’autorisation explicite des systèmes ciblés.
</p>

<hr/>

<h2>📁 Configuration</h2>
<ul>
  <li><code>ReverseShellHandler.conf</code> : hôte/port, auto-connect, Proxy (type/hôte/port/user/pass), MP3 (activé + chemin).</li>
</ul>

<hr/>

<h2>🧩 Générateur de payloads — exemples (résumé)</h2>
<ul>
  <li><strong>Windows / Reverse Shell (PowerShell)</strong> — une one-liner PS non-interactive avec boucle de lecture/écriture et écho du prompt courant.</li>
  <li><strong>Linux / Meterpreter</strong> — appels <code>msfvenom</code> ciblés par arch (x86/x64/ARM/AArch64) pour ELF.</li>
  <li><strong>Bash</strong> — redirections <code>/dev/tcp</code> classiques.</li>
  <li><strong>Encodage PS</strong> — <code>-enc</code> en UTF-16LE sur la partie commande, conforme à PowerShell.</li>
</ul>

<hr/>

<h2>📸 Captures d'écran (placeholders)</h2>
<p>
  <img alt="Dashboard" src="docs/screenshot_dashboard.png"/>
  <img alt="Terminals" src="docs/screenshot_terminals.png"/>
  <img alt="Bulk Whois" src="docs/screenshot_whois.png"/>
  <img alt="Payload Generator" src="docs/screenshot_payloads.png"/>
</p>
