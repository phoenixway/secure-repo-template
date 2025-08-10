#!/bin/bash
#
# Скрипт для налаштування середовища розробки Python.
# Створює віртуальне оточення та встановлює залежності.
#

# Зупиняємо виконання при першій помилці
set -e

# --- Кольори для виводу ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() { echo -e "${BLUE}[i] $1${NC}"; }
echo_success() { echo -e "${GREEN}[✓] $1${NC}"; }
echo_warning() { echo -e "${YELLOW}[!] $1${NC}"; }

# --- Крок 1: Перевірка наявності Python 3 ---
echo_info "Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[✗] Python 3 is not installed. Please install Python 3 to continue.${NC}"
    exit 1
fi
echo_success "Python 3 found."

# --- Крок 2: Створення віртуального оточення ---
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo_info "Creating Python virtual environment in './$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    echo_success "Virtual environment created."
else
    echo_info "Virtual environment './$VENV_DIR' already exists. Skipping creation."
fi

# --- Крок 3: Встановлення залежностей ---
REQUIREMENTS_FILE="requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}[✗] '$REQUIREMENTS_FILE' not found! Cannot install dependencies.${NC}"
    exit 1
fi

echo_info "Installing dependencies from '$REQUIREMENTS_FILE'..."
# Використовуємо pip з нашого віртуального оточення
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
echo_success "Dependencies installed successfully."

# --- Крок 4: Інструкції з активації ---
echo_info "------------------------------------------------------------------"
echo_success "Setup complete!"
echo_info "To activate the virtual environment, run the following command"
echo_info "in your current terminal session:"
echo_info ""

# Визначаємо поточну оболонку (shell)
CURRENT_SHELL=$(basename "$SHELL")

case "$CURRENT_SHELL" in
bash|zsh)
    echo -e "  For ${YELLOW}bash/zsh${NC}:"
    echo -e "    ${GREEN}source $VENV_DIR/bin/activate${NC}"
    ;;
fish)
    echo -e "  For ${YELLOW}fish${NC}:"
    echo -e "    ${GREEN}source $VENV_DIR/bin/activate.fish${NC}"
    ;;
*)
    echo -e "  ${YELLOW}Could not detect your shell.${NC} Please use the activation script"
    echo -e "  for your shell located in the './$VENV_DIR/bin/' directory."
    ;;
esac

echo_info ""
echo_info "After activation, you can run the application with:"
echo_info "  python manager.py --help"
echo_info "------------------------------------------------------------------"