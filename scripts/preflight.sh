#!/usr/bin/env bash
# RATISS LABS AGENT — preflight (MONTAGE.md étape 1 / PROMPT GLM étape A)
# Vérifie les prérequis de l'hôte SANS installer quoi que ce soit et SANS démarrer de service.
# Sortie : une ligne par contrôle, résumé final, code 0 si tout va bien, 1 sinon.
# Usage : bash scripts/preflight.sh

set -u

COMPT_OK=0
COMPT_FAIL=0
COMPT_WARN=0

ok()   { printf '  [OK]   %s\n' "$1"; COMPT_OK=$((COMPT_OK+1)); }
fail() { printf '  [ÉCHEC] %s\n' "$1"; COMPT_FAIL=$((COMPT_FAIL+1)); }
warn() { printf '  [INFO] %s\n' "$1"; COMPT_WARN=$((COMPT_WARN+1)); }

version_ge() {
  # version_ge A B -> 0 si A >= B (comparaison d'entiers pointés, ex: 22.19)
  printf '%s\n%s\n' "$2" "$1" | sort -V | head -1 | grep -qx "$2"
}

port_libre() {
  # port_libre N -> 0 si personne n'écoute sur 127.0.0.1:N
  ! (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null
}

titre() { printf '\n== %s ==\n' "$1"; }

titre "Docker"
if ! command -v docker >/dev/null 2>&1; then
  fail "Docker absent — installer Docker Desktop (Windows/macOS) ou docker engine (Linux)"
else
  ok "Docker présent : $(docker --version 2>/dev/null | head -1)"
  if docker info >/dev/null 2>&1; then
    ok "Docker daemon démarré"
  else
    fail "Docker présent mais daemon NON démarré — lancer Docker Desktop / systemctl start docker"
  fi
  if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose v2 : $(docker compose version 2>/dev/null | head -1)"
  else
    fail "Docker Compose v2 absent (commande 'docker compose' introuvable)"
  fi
fi

titre "Python"
if command -v python3 >/dev/null 2>&1; then
  PYV="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)"
  if version_ge "$PYV" "3.12"; then
    ok "Python $PYV (requis : 3.12, VERSIONS.md)"
  else
    fail "Python $PYV — 3.12 requis (ContextForge exige >= 3.12 et < 3.14)"
  fi
else
  fail "python3 absent"
fi

titre "Node.js"
if command -v node >/dev/null 2>&1; then
  NV="$(node --version 2>/dev/null | sed 's/^v//')"
  if version_ge "$NV" "22.19"; then
    ok "Node $NV (requis : >= 22.19, MCP Inspector 2.9.0)"
  else
    fail "Node $NV — >= 22.19 requis"
  fi
else
  fail "node absent (requis >= 22.19)"
fi

titre "Ressources"
if [ -r /proc/meminfo ]; then
  MEM_KB="$(awk '/MemAvailable/ {print $2}' /proc/meminfo)"
  MEM_GIO=$((MEM_KB / 1024 / 1024))
  if [ "$MEM_GIO" -ge 8 ]; then
    ok "Mémoire disponible : ${MEM_GIO} Gio (>= 8 Gio)"
  else
    fail "Mémoire disponible : ${MEM_GIO} Gio (< 8 Gio) — fermer des applications ou augmenter la RAM/WSL2"
  fi
else
  warn "MemAvailable illisible (non-Linux ?) — le contrôle mémoire complet sera fait par preflight.ps1"
fi
DISK_GIO="$(df -BG --output=avail "$PWD" 2>/dev/null | tail -1 | tr -dc '0-9')"
if [ -n "$DISK_GIO" ]; then
  if [ "$DISK_GIO" -ge 20 ]; then
    ok "Disque disponible : ${DISK_GIO} Go (>= 20 Go)"
  else
    fail "Disque disponible : ${DISK_GIO} Go (< 20 Go)"
  fi
else
  fail "Espace disque illisible"
fi

titre "Ports (5432, 6379, 9000, 9001 sur 127.0.0.1)"
for P in 5432 6379 9000 9001; do
  if port_libre "$P"; then
    ok "Port $P libre"
  else
    fail "Port $P OCCUPÉ — libérer le port ou changer la variable correspondante dans .env"
  fi
done

titre "KVM (information seulement)"
if [ -e /dev/kvm ]; then
  warn "/dev/kvm présent — accélération virtuelle disponible (utile à des runtimes VM, pas requis en V1)"
else
  warn "/dev/kvm absent — information seulement, rien de requis en V1"
fi

titre "gVisor / runsc (information seulement)"
if command -v runsc >/dev/null 2>&1 || docker info 2>/dev/null | grep -q runsc; then
  warn "runsc détecté — le sandbox Python pourra utiliser gVisor (étape G)"
else
  warn "runsc absent — attendu sur la plupart des postes ; l'étape G le déclarera, sinon sandbox limitée (Windows/macOS : Docker standard, isolation plus faible)"
fi

titre "Résumé"
printf '  OK: %d   ÉCHEC: %d   INFO: %d\n' "$COMPT_OK" "$COMPT_FAIL" "$COMPT_WARN"
if [ "$COMPT_FAIL" -gt 0 ]; then
  echo "  -> preflight : ÉCHEC. Corriger les points en ÉCHEC avant 'make up'."
  exit 1
fi
echo "  -> preflight : PASS. Aucun service n'a été démarré ni installé par ce script."
