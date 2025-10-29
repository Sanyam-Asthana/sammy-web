import requests
import sys
from tqdm.auto import tqdm
import concurrent.futures
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
import os
import webbrowser

dirs = []
try:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Sammy/0.1.3 (https://github.com/sanyam/sammy)",
            "Accept-Language": "en-US,en;q=0.5",
        }
    )
except Exception as e:
    print(f"Error creating session: {e}")
    sys.exit(1)


def getStatus(url):
    print("=" * 40)
    try:
        response = session.get(url, timeout=5)
        print("Status Code:", response.status_code)

        if response.status_code == 200:
            print("OK")
        elif response.status_code == 404:
            print("Could not connect!")
        else:
            print("Unknown status code!")

        print("=" * 40)
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error getting status: {e}")
        print("=" * 40)
        return -1


header = {}


def getHeader(url):
    global header
    try:
        response = session.get(url, timeout=5)
        print("=" * 16 + "HEADERS" + "=" * 17)
        for k in response.headers:
            print(k, end=": ")
            print(response.headers[k])
            header.update({k: response.headers[k]})
        print("=" * 40)
    except requests.exceptions.RequestException as e:
        print(f"Error getting header: {e}")


def getText(url):
    try:
        response = session.get(url, timeout=5)
        print("=" * 18 + "TEXT" + "=" * 18)
        print(response.text)
        print("=" * 40)
    except requests.exceptions.RequestException as e:
        print(f"Error getting text: {e}")


def check_path(path):
    global dirs
    global url

    s = url + "/" + path
    try:
        response = session.get(s, timeout=5)
        if response.status_code == 200:
            dirs.append(s)
            return s
    except requests.exceptions.RequestException:
        pass

    return None


crawled_links = []


def run_crawler(base_url):
    print("=" * 17 + "CRAWLER" + "=" * 18)
    try:
        links_to_visit = set([base_url])
        visited_links = set()

        home_domain = urlparse(base_url).netloc

        print(f"Starting crawl on domain: {home_domain}")

        while links_to_visit:
            current_link = links_to_visit.pop()

            if current_link in visited_links:
                continue

            visited_links.add(current_link)

            try:
                response = session.get(current_link, timeout=5)
                if "text/html" not in response.headers.get("content-type", ""):
                    continue

                print(f"[+] Found Page: {current_link}")

                found_hrefs = re.findall(r'href="([^"]*)"', response.text)

                for href in found_hrefs:
                    if href.startswith("#") or href.startswith("mailto:"):
                        continue

                    new_link = urljoin(current_link, href)

                    clean_new_link = (
                        urlparse(new_link)._replace(query="", fragment="").geturl()
                    )

                    if (
                        urlparse(new_link).netloc == home_domain
                        and clean_new_link not in visited_links
                    ):
                        links_to_visit.add(clean_new_link)

            except requests.exceptions.RequestException as e:
                print(f"[!] Failed to crawl {current_link}: {e}")

        print("=" * 40)
        print(f"--- Crawl Complete. Found {len(visited_links)} pages. ---")
        for link in sorted(list(visited_links)):
            print(link)
            crawled_links.append(link)
        print("=" * 40)

    except Exception as e:
        print(f"An error occurred during crawl: {e}")


server_software = ""


def getServer():
    global header
    global server_software
    server_string = header.get("Server")

    if server_string:
        server_string = server_string.lower()

        if "nginx" in server_string:
            print("Server Software: Nginx")
            server_software = "Nginx"

        elif "apache" in server_string:
            print("Server Software: Apache")
            server_software = "Apache"

        elif "iis" in server_string or "microsoft-iis" in server_string:
            print("Server Software: Microsoft IIS")
            server_software = "Microsoft IIS"

        elif "cloudflare" in server_string:
            print("Server Software: Cloudflare (Hides the real server)")
            server_software = "Cloudflare"

        elif "gws" in server_string:
            print("Server Software: Google Web Server")
            server_software = "Google Web Server"

        elif "litespeed" in server_string:
            print("Server Software: LiteSpeed")
            server_software = "LiteSpeed"

        else:
            print(f"Server Software: {server_string.capitalize()}")
            server_software = server_string.capitalize()
    else:
        print("Server Software: Unknown (No 'Server' header found)")
        server_software = "Unknown"


backend = ""


def getBackend():
    global header
    global backend
    backend_string = header.get("X-Powered-By")

    if backend_string:
        backend_string = backend_string.lower()

        if "php" in backend_string:
            print("Backend Language: PHP")
            backend = "PHP"

        elif "asp.net" in backend_string:
            print("Backend Language: ASP.NET")
            backend = "ASP.NET"

        elif "express" in backend_string:
            print("Backend Language: Express (Node.js)")
            backend = "Node.js"

        elif "django" in backend_string:
            print("Backend Language: Django (Python)")
            backend = "Django"

        elif "next.js" in backend_string:
            print("Backend Language: Next.js (Node.js)")
            backend = "Next.js"

        else:
            print(f"Backend Language: {backend_string.capitalize()}")
            backend = backend_string.capitalize()
    else:
        print("Backend Language: Unknown (No 'X-Powered-By' header found)")
        backend = "Unknown"


comments = []


def getComments(txt):
    global comments
    try:
        toFind = "<!--"
        ind = txt.find(toFind)
        print("=" * 16 + "COMMENTS" + "=" * 16)
        if ind == -1:
            print("No comments found.")

        while ind != -1:
            end_comment = txt.find("-->", ind)
            if end_comment == -1:
                break
            comment_text = txt[ind + 4 : end_comment].strip()
            if comment_text:
                print(f"[+] {comment_text}")
                comments.append(comment_text)
            ind = txt.find(toFind, end_comment)
        print("=" * 40)
    except Exception as e:
        print(f"Error grabbing comments: {e}")


def main():
    global url
    global session

    if len(sys.argv) == 1:
        print("Sammy V0.1.3")
        print(
            "Usage: sammy [url] -h(eaders) | -t(ext) | -f(shell) | -d(irs) | -c(rawl) | -r(eport)"
        )
        sys.exit(0)

    url = sys.argv[1]

    print("  /$$$$$$                                                 ")
    print(" /$$__  $$                                                ")
    print("| $$  \\__/  /$$$$$$  /$$$$$$/$$$$  /$$$$$$/$$$$  /$$   /$$")
    print("|  $$$$$$  |____  $$| $$_  $$_  $$| $$_  $$_  $$| $$  | $$")
    print(" \\____  $$  /$$$$$$$| $$ \\ $$ \\ $$| $$ \\ $$ \\ $$| $$  | $$")
    print(" /$$  \\ $$ /$$__  $$| $$ | $$ | $$| $$ | $$ | $$| $$  | $$")
    print("|  $$$$$$/|  $$$$$$$| $$ | $$ | $$| $$ | $$ | $$|  $$$$$$$")
    print(" \\______/  \\_______/|__/ |__/ |__/|__/ |__/ |__/ \\____  $$")
    print("                                                 /$$  | $$")
    print("                                                |  $$$$$$/")
    print("                                                 \\______/ ")
    print()
    print("By Sanyam Asthana, 2025")
    print("Version 0.1.3")

    print("Sammy initiated on URL:", url)

    print("=" * 40)
    try:
        response = session.get(url, timeout=5)
        print("Status Code:", response.status_code)

        if response.status_code == 200:
            print("OK")
        elif response.status_code == 404:
            print("Could not connect!")
        else:
            print("Unknown status code!")

    except requests.exceptions.RequestException as e:
        print(f"[!] Fatal Error connecting to base URL: {e}")
        print("=" * 40)
        sys.exit(1)
    print("=" * 40)

    if "-h" in sys.argv:
        print("=" * 16 + "HEADERS" + "=" * 17)
        for k in response.headers:
            print(k, end=": ")
            print(response.headers[k])
        print("=" * 40)

    if "-t" in sys.argv:
        print("=" * 18 + "TEXT" + "=" * 18)
        print(response.text)
        print("=" * 40)

    if "-d" in sys.argv:
        print("=" * 14 + "DIRECTORIES" + "=" * 15)

        try:
            NUM_THREADS = int(
                input(
                    "Number of threads (Default is 20) (A higher number of threads may result in rate limiting): "
                )
            )
        except:
            NUM_THREADS = 20

        print(f"Searching with {NUM_THREADS} threads...")
        path_list = []

        package_dir = Path(__file__).parent
        wordlist_path = package_dir / "wordlist.txt"

        try:
            with open(wordlist_path, "r") as F:
                for line in F:
                    path = line.strip()
                    if path:
                        path_list.append(path)
        except FileNotFoundError:
            print("[!] Error: wordlist.txt not found.")
            sys.exit(1)

        if not path_list:
            print("[!] Wordlist is empty.")
            sys.exit(1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            results = list(
                tqdm(
                    executor.map(check_path, path_list),
                    total=len(path_list),
                    desc="Checking",
                    unit="path",
                )
            )

        print("\n" + "=" * 40)
        print("--- Scan Complete. Found: ---")

        found_something = False
        for path in results:
            if path:
                print(f"[+] {path}")
                found_something = True

        if not found_something:
            print("No directories or files found.")

        print("=" * 40)

    if "-c" in sys.argv:
        run_crawler(url)

    if "-f" in sys.argv:
        x = 1
        path = url
        while x:
            s = path + ": "
            inp = input(s)

            if inp.startswith("cd "):
                new_path = urljoin(path, inp.split()[1])
                if getStatus(new_path) == 200:
                    print(f"Moved to: {new_path}")
                    path = new_path
                else:
                    print("Could not move to the new path!")

            elif inp == "cd/":
                path = url
                getStatus(path)

            elif inp == "text":
                getText(path)

            elif inp == "cookies":
                print("=" * 16 + "COOKIES" + "=" * 17)
                if not session.cookies:
                    print("No cookies in session.")
                else:
                    for cookie in session.cookies:
                        print(f"  Name  : {cookie.name}")
                        print(f"  Value : {cookie.value}")
                        print(f"  Domain: {cookie.domain}")
                        print("  ----------")
                print("=" * 40)

            elif inp.startswith("grabfield "):
                try:
                    txt = session.get(path).text
                    toFind = inp.split()[1]
                    print("=" * 16 + toFind + "=" * 17)

                    pattern = f'{toFind}="([^"]*)"'
                    matches = re.findall(pattern, txt)

                    if not matches:
                        print("No matches found.")

                    for match in set(matches):
                        print(f"[+] {match}")

                    print("=" * (33 + len(toFind)))
                except Exception as e:
                    print(f"Error grabbing field: {e}")

            elif inp == "comments":
                txt = session.get(path).text
                getComments(txt)

            elif inp == "ls":
                if len(dirs) == 0:
                    print(
                        "Directories not scanned or not found! Re-run with -d to scan directories!"
                    )
                else:
                    print("=" * 14 + "DIRECTORIES" + "=" * 15)
                    for i in dirs:
                        print(i)
                    print("\n" + "=" * 40)

            elif inp == "exit":
                x = 0

    if "-r" in sys.argv:
        with open("report.html", "w") as F:
            pass

        with open("report.html", "a") as F:
            getHeader(url)
            getServer()
            getBackend()
            F.write(f"""
                <html>
                <head>
                <title>{url}</title>
                </head>
                <body>
                <h1>Sammy</h1>
                <h2>Analysis of: {url}</h2>
                <hr>
                <h2>Key Insights</h2>
                <ul>
                """)

            F.write(f"""
                <li>Server Software: {server_software}</li>
                <li>Backend Technology: {backend}</li>
                </ul>
                """)

            F.write("""
                <h2>Crawled Links:</h2>
                <ul>
                """)

            run_crawler(url)

            for crawled_link in crawled_links:
                F.write(f"<li><a href={crawled_link}>{crawled_link}</a></li>\n")

            F.write("""
                </ul>
                <br>
                <h2>Header of base URL:</h2>
                """)

            for header_line in header:
                st = header_line + ": " + header[header_line]
                F.write(st + "<br>")

            st = url + "/robots.txt"
            resp = requests.get(st)
            if resp.status_code == 200:
                F.write(f"""
                    <h2>robots.txt:</h2>
                    {resp.text}
                    """)

            global comments
            F.write("""
                <h2>Comments:</h2>
                <ul>
                """)

            for crawled_link in crawled_links:
                getComments(requests.get(crawled_link).text)
                F.write(f"""<li><a href="{crawled_link}">{crawled_link}</a>:</li>""")
                F.write("<ul>")
                for comment in comments:
                    F.write(f"<li>{comment}</li>")
                F.write("</ul>")
                comments = []

            F.write("</ul>")

            F.write("""
            </body>
            </html>
            """)

            print(header)
            webbrowser.open("file://" + os.getcwd() + "/report.html")


if __name__ == "__main__":
    main()
