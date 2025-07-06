import subprocess
import os

SITE_DIR = "/home/anza/suggestoai-site"

def git_publish():
    # Έλεγχος αν το repo υπάρχει
    if not os.path.isdir(SITE_DIR):
        print(f"❌ Το site repo δεν βρέθηκε στο {SITE_DIR}. Βεβαιώσου ότι το έχεις κλωνοποιήσει σωστά!")
        print("Αν χρειάζεται να αλλάξεις το path, ενημέρωσέ με!")
        return
    try:
        # Check for uncommitted changes
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=SITE_DIR).decode().strip()
        if not status:
            print("[Site] No changes to commit.")
            return
        subprocess.run(["git", "add", "."], cwd=SITE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Add new AI product post"], cwd=SITE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_DIR, check=True)
        print("✅ Το νέο post ανέβηκε στο site σου (GitHub Pages)!")
        print("Αν δεν εμφανίζεται άμεσα, περίμενε λίγα λεπτά για να γίνει deploy από το GitHub.")
    except subprocess.CalledProcessError as e:
        print("❌ Κάτι πήγε στραβά με το git push:", e)
        print("Αν δεις error για permissions ή SSH, βεβαιώσου ότι το SSH key σου είναι σωστά ρυθμισμένο στο GitHub.")
        print("Αν χρειάζεται να προσθέσεις το public SSH key στο repo ή να αλλάξεις config, ενημέρωσέ με να σου γράψω μήνυμα για τον AI του site!") 