# sammy-web
Sammy is a simple CLI program with web pentesting tools

### How to use:
1. Install the package with `pip install sammy-web`
2. In terminal, type `sammy` to confirm the installation.

Type `sammy [url]` to initiate sammy on the specified URL.

#### Flags:
1. `-h`: Displays the Request Headers when loading the site.
2. `-t`: Displays rhe Requested Text when loading the site.
3. `-d`: Initiates the process of brute-forcing web-directories of the URL. Comes pre-installed with a wordlist with 9400+ entries.
4. `-f`: Enters the interactable mode.

Example usage: `sammy https://scanme.nmap.org -h -d`
