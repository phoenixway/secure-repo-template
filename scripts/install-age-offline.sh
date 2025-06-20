#!/bin/bash
set -e

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

echo "[✓] age і age-keygen встановлено у $INSTALL_DIR"
