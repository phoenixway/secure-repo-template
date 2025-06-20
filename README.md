# 🔐 Secure Repo Template

This repository provides a hardened template for managing **encrypted personal data** (markdown, source code, sensitive text) inside a Git repository.  
It is designed to be resistant to:

- Physical attacks on your device
- Compromised or untrustworthy cloud providers
- Remote screen/keyboard surveillance (when encryption is properly handled)

---

## 🧭 Purpose of the Template

This template helps you:

- Version-control sensitive documents using Git
- Encrypt files using [age](https://github.com/FiloSottile/age)
- Separate public and private data
- Store encrypted backups in hostile or public environments
- Minimize risk of accidental leaks, even if repo is public

---

## 🧰 Setup the Repository (For Beginners)
Follow these steps to create a new encrypted personal repository from this template:

---

### 1. 📁 Create a New Repository from Template

Click **“Use this template”** on the GitHub page  
→ Choose a name like `my-secure-notes`  
→ Clone it:

```bash
git clone --depth=1 https://github.com/phoenixway/secure-repo-template.git my-secure-notes
cd my-secure-notes
```

### 2. Generate a new age key
```bash
age-keygen -o age-key.txt
```

🔐 **Important**: Never commit age-key.txt. It contains your private key.

### 3. Optional: 🌐 Connecting to GitHub (Creating or Adding a Remote)
Once you've initialized or cloned this repository locally, you can connect it to a GitHub repository to store the encrypted content remotely.
#### 🆕 A. Create a New GitHub Repository

1. Go to [https://github.com/new](https://github.com/new)
2. Name it something like `my-secure-notes`
3. Leave it **empty** (no README, no .gitignore, no license)
4. Click **Create repository**

Then in your local terminal:

```bash
git remote add origin git@github.com:yourusername/my-secure-notes.git
# or If you're using HTTPS instead of SSH:
git remote add origin https://github.com/yourusername/my-secure-notes.git

git branch -M main
git push -u origin main
```

#### B. Connect to an Existing Repository
If you already have a GitHub repository created, connect it like this:
```bash
git remote add origin git@github.com:yourusername/existing-repo.git
git push -u origin main
```

##### C. 🧪 Check Connection
To confirm that your GitHub remote is set up:

```bash
git remote -v
```

You should see something like:

```perl
origin  git@github.com:yourusername/my-secure-notes.git (fetch)
origin  git@github.com:yourusername/my-secure-notes.git (push)
```

🔐 Don’t worry: the encrypted files are safe to store even in a public GitHub repository, as long as you do not upload age-key.txt.


### 3. ☁️ Optional: Configure Cloud Backup

Install and configure rclone:

```bash
rclone config
```

Then edit .env in your repository:

```dotenv
CLOUD_REMOTES="gdrive:secure-notes dropbox:vault backup1:/mnt/encrypted"
```

Run test saving:

```bash
bash scripts/push-to-clouds.sh
```

This sends an encrypted archive of your repository to all configured cloud destinations.

## ✍️ Working with Your Notes
### Option A: Manual encryption flow
1. Create/edit one or more .md files (except README.md).
2. Encrypt & remove originals:

```bash
bash scripts/encrypt-unencrypted.sh
```

3.Push manually.

```bash
git add *.md.age
git commit -m "Encrypted notes"
git push
```
### Option B: All-in-one automation
Run this after any edit:

```bash
bash scripts/encrypt-n-store.sh
```

This will:
    * Encrypt all unencrypted .md files (except README.md)
    * Securely destroy the originals
    * Commit changes
    * Push to your Git remote (if configured)
    * Create encrypted archive and push it to cloud remotes (push-to-clouds.sh)

## 🔓 Accessing Decrypted Content
To work with existing encrypted files:
1. Run:

```bash
bash scripts/decrypt-n-work.sh
```

2. Select one or more encrypted files to decrypt using interactive fzf.
3. Edit the decrypted file.
4. After editing, take care to encrypt your data, wipe out originals, move encrypted data to cloud stores. That can be done manually, semi-manually (using encrypt-unencrypted.sh and push-to-clouds.sh) or by:

```bash 
bash scripts/encrypt-n-store.sh
```

## ☁️ Cloud Backup (Optional)
### Backing up to cloud
Cloud destinations are defined in .env under CLOUD_REMOTES. Example:
```dotenv
CLOUD_REMOTES="cloud1:secure-repo-backups cloud2:mirror/secure cloud3:encrypted/vaults"
```

To encrypt and upload current state:
```bash
bash scripts/push-to-clouds.sh
```

This creates a full encrypted .tar.gz.age archive and sends it to all remotes via rclone.

### Restoring from cloud
о
```

* Lists available .tar.gz.age backups from remote
* Downloads and decrypts the one you choose
* Extracts it to a safe folder for inspection

To create a backup encrypted archive and upload it via rclone:

```bash
bash scripts/backup-to-cloud.sh
```


## 🔥 Security Practices
* Never commit age-key.txt or .env
* Avoid working on decrypted files unless needed
* Avoid leaving decrypted files on disk
* Run encrypting scripts immediately after editing any file
* Periodically test restoring from encrypted backup
* Store backups in multiple cloud services for redundancy
* Periodically test restore-from-cloud.sh

## 📂 Directory Layout
```pgsql
├── README.md              ← public description
├── *.md                   ← your notes (ignored by Git)
├── *.md.age               ← encrypted notes (in Git)
├── age-key.txt            ← your private key (ignored)
├── backup/                ← encrypted archives
├── scripts/               ← public automation
├── personal-scripts/      ← your local private logic
└── .env                   ← local-only config (ignored)
```

## ✅ Requirements
* age
* rclone (for backups)
* fzf (optional but useful)