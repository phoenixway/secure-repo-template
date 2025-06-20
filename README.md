# 🔐 Secure Repo Template

This repository provides a hardened template for managing **encrypted personal data** (source code, markdown, whatever) inside a Git repository.  
It is designed to be resistant to:

- Physical attacks on your device
- Compromised or untrustworthy cloud providers
- Remote access or monitoring (if encryption is properly handled)

---

## 🧭 Purpose of the Template

This template helps you:

- Keep sensitive notes and documents under version control
- Encrypt each file individually using [age](https://github.com/FiloSottile/age)
- Separate public vs private content clearly
- Make backups that are safe to store in hostile environments (even public Git repositories under some kinds of attacks)

---

## 🛠 How to Use the Template

1. **Clone this repository as a template:**

```bash
git clone --depth=1 https://github.com/phoenixway/secure-repo-template.git my-secure-notes
cd my-secure-notes
```

2. **Generate a new age key:**
```bash
age-keygen -o age-key.txt
```

Store this file outside of Git. It contains your private key.

3. **Create your encrypted notes:**

Edit or create files like my-note.md, then run:

```bash
bash scripts/encrypt-n-store.sh
```

This will:
    * Encrypt each .md file (except README.md)
    * Securely shred the plaintext
    * Commit the .md.age files
    * Push to your Git remote if configured

4. **Add to remote:**

    ```bash
    git remote add origin git@github.com:youruser/my-secure-notes.git
    git push -u origin main
    ```

## 🔓 Accessing Decrypted Content
To view or edit a file:

1. Run:

```bash
bash scripts/decrypt-n-work.sh
```

2. Select one or more encrypted files to decrypt using interactive fzf.
3. Edit the decrypted file.
4. After you are done, securely delete the decrypted file:

```bash
shred -u filename.md
```

## ☁️ Cloud Backup (Optional)
To create a backup encrypted archive and upload it via rclone:

```bash
bash scripts/backup-to-cloud.sh
```

This encrypts the entire repository (*.md.age, README.md, .git) and sends it to a configured rclone remote.
Make sure you’ve configured your rclone remote first with:

```bash
rclone config
```

## 🔥 Security Practices
* Never commit age-key.txt to Git
* Avoid working on decrypted files unless needed
* Use shred -u after every edit
* Periodically test restoring from encrypted backup
* Store backups in multiple cloud services for redundancy

## 📂 Directory Layout
```pgsql
├── README.md              ← public description
├── *.md                   ← your notes (ignored by Git)
├── *.md.age               ← encrypted notes (in Git)
├── age-key.txt            ← your private key (ignored)
├── backup/                ← encrypted archives
├── scripts/               ← public automation
└── personal-scripts/      ← your local private logic
```

## ✅ Requirements
* age
* rclone (for backups)
* fzf (optional but useful)