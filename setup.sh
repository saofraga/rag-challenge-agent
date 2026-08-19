#!/usr/bin/env bash
# Setup do ambiente para o Challenge RAG — BimBam Buy Assistant
# Verifica e instala as ferramentas necessárias para desenvolver, testar e fazer deploy do projeto.

set -e

echo "== Verificando Python =="
if ! command -v python3 &> /dev/null; then
  echo "python3 não encontrado. Instale Python 3.11+ antes de continuar (https://www.python.org/downloads/)."
  exit 1
fi
python3 --version

echo ""
echo "== Criando ambiente virtual (.venv) =="
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Ambiente virtual criado em .venv"
else
  echo ".venv já existe, pulando criação."
fi

echo ""
echo "== Instalando dependências Python (requirements.txt) =="
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo "Dependências instaladas dentro de .venv."

echo ""
echo "== Verificando Node.js e Vercel CLI (para deploy) =="
if ! command -v node &> /dev/null; then
  echo "Node.js não encontrado. Instale em https://nodejs.org/ antes de fazer deploy no Vercel."
else
  echo "Node encontrado: $(node --version)"
  if ! command -v vercel &> /dev/null; then
    echo "Instalando Vercel CLI globalmente (npm install -g vercel)..."
    npm install -g vercel
  else
    echo "Vercel CLI já instalada: $(vercel --version)"
  fi
fi

echo ""
echo "== Verificando GitHub CLI (para publicar issues e criar o repositório) =="
if ! command -v gh &> /dev/null; then
  echo "gh (GitHub CLI) não encontrado. Instale em https://cli.github.com/ para criar o repositório e publicar as issues do spec/tickets."
else
  echo "gh encontrado: $(gh --version | head -1)"
  gh auth status 2>&1 || echo "Rode 'gh auth login' para autenticar antes de criar o repositório."
fi

echo ""
echo "== Setup concluído =="
echo "Próximos passos: leia o README.md para instruções de execução local."
echo "Ative o ambiente virtual em novas sessões de terminal com: source .venv/bin/activate"
