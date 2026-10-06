import base64
import time
import requests

# ================= CONFIGURAZIONE =================
TOKEN = "secret token"

OWNER = "username"
REPO = "your repo"
MAIN_BRANCH = "main"  
TOTAL_ITERATIONS = 1000
# ===================================================

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"


def get_latest_commit_sha():
    url = f"{BASE_URL}/git/ref/heads/{MAIN_BRANCH}"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()["object"]["sha"]


def get_readme_info():
    url = f"{BASE_URL}/contents/README.md"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    data = res.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def create_branch(new_branch_name, sha):
    url = f"{BASE_URL}/git/refs"
    payload = {"ref": f"refs/heads/{new_branch_name}", "sha": sha}
    res = requests.post(url, json=payload, headers=HEADERS)
    res.raise_for_status()


def update_readme_in_branch(branch_name, current_content, sha, iteration):
    new_content = current_content + f"Hello World! #{iteration}\n"
    encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    url = f"{BASE_URL}/contents/README.md"
    payload = {
        "message": f"docs: aggiungi Hello World! #{iteration}",
        "content": encoded_content,
        "sha": sha,
        "branch": branch_name,
    }
    res = requests.put(url, json=payload, headers=HEADERS)
    res.raise_for_status()


def create_pull_request(branch_name, iteration):
    url = f"{BASE_URL}/pulls"
    payload = {
        "title": f"Aggiunta Hello World! #{iteration}",
        "head": branch_name,
        "base": MAIN_BRANCH,
        "body": f"Merge automatico per l'iterazione {iteration}",
    }
    res = requests.post(url, json=payload, headers=HEADERS)
    res.raise_for_status()
    return res.json()["number"]


def merge_pull_request(pr_number):
    url = f"{BASE_URL}/pulls/{pr_number}/merge"
    payload = {"merge_method": "merge"}
    res = requests.put(url, json=payload, headers=HEADERS)
    res.raise_for_status()


def delete_branch(branch_name):
    url = f"{BASE_URL}/git/refs/heads/{branch_name}"
    requests.delete(url, headers=HEADERS)


def run_bot():
    print(f"Avvio del ciclo di {TOTAL_ITERATIONS} modifiche...")

    i = 1
    while i <= TOTAL_ITERATIONS:
        timestamp = int(time.time())
        branch_name = f"modifica-{i}-{timestamp}"
        print(f"\n--- [Iterazione {i}/{TOTAL_ITERATIONS}] ---")

        try:
            main_sha = get_latest_commit_sha()
            content, readme_sha = get_readme_info()

            create_branch(branch_name, main_sha)
            print(f"1. Branch '{branch_name}' creato.")

            update_readme_in_branch(branch_name, content, readme_sha, i)
            print("2. Scritto 'Hello World!' e fatto il commit.")

            pr_num = create_pull_request(branch_name, i)
            print(f"3. PR #{pr_num} creata.")

            merge_pull_request(pr_num)
            print("4. Merge completato sul main!")

            delete_branch(branch_name)
            print("5. Branch pulito.")

            i += 1

        except requests.exceptions.HTTPError as err:
            print(f"Errore HTTP all'iterazione {i}: {err}")
            print("Pulizia branch e attesa di 5 secondi prima di riprovare...")
            try:
                delete_branch(branch_name)
            except Exception:
                pass
            time.sleep(5)

        except Exception as e:
            print(f"Errore generico all'iterazione {i}: {e}")
            time.sleep(5)

        time.sleep(2)


if __name__ == "__main__":
    run_bot()
