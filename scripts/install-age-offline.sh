#!/bin/bash
set -e
# TODO: sha256sum age-v1.1.1-linux-amd64.tar.gz check
# 3a21eae4c0048e4e946db4a54ff857d848f3e9c276d351c1571ad46cfb8270b1
# 

# Шлях, куди встановити
INSTALL_DIR="$HOME/.local/bin"

# Створюємо директорію, якщо її нема
mkdir -p "$INSTALL_DIR"

# Копіюємо бінарники (перед цим витягни їх з архіву)
cp ./age "$INSTALL_DIR/"
cp ./age-keygen "$INSTALL_DIR/"

# Дозволяємо виконання
chmod +x "$INSTALL_DIR/age" "$INSTALL_DIR/age-keygen"

# Додаємо до PATH у поточному сеансі
export PATH="$INSTALL_DIR:$PATH"

# Додаємо до ~/.bashrc або ~/.zshrc
SHELLRC="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ]; then
  SHELLRC="$HOME/.zshrc"
fi

if ! grep -q "$INSTALL_DIR" "$SHELLRC"; then
  echo "export PATH=\"$INSTALL_DIR:\$$PATH\"" >> "$SHELLRC"
  echo "[✓] Додано $INSTALL_DIR до PATH у $SHELLRC"
fi

echo "Trying to check hash.."
sha256sum -c age.sha256

echo "[✓] age і age-keygen встановлено у $INSTALL_DIR"