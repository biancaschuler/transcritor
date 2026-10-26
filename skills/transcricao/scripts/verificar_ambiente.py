#!/usr/bin/env python3
"""
Confere se a máquina tem o que a skill transcricao precisa e diz como instalar o que
faltar, com o comando do sistema de quem está usando (Windows, macOS ou Linux).

Uso:
    python verificar_ambiente.py

Roda com qualquer Python 3.6 ou mais novo e só com a biblioteca padrão, para conseguir
avisar até quando o Python é velho demais. A linha PYTHON= diz qual Python tem o
faster-whisper, e a última linha é AMBIENTE_OK=1 quando dá para transcrever ou
AMBIENTE_OK=0 quando falta algo obrigatório.

O faster-whisper vai num ambiente virtual em ~/.transcritor/venv, separado do Python
do sistema. No macOS e no Linux o Python do sistema recusa pip install direto, e no
Windows o ambiente separado evita conflito com outros programas. O transcrever.py
acha esse ambiente sozinho.

As mensagens ficam em ASCII porque o console do Windows nem sempre está em UTF-8.

Código de saída. 0 com tudo pronto e 1 quando falta algo obrigatório.
"""
import glob
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SISTEMA = platform.system()  # Windows, Darwin (macOS) ou Linux
MODELO = os.environ.get("WHISPER_MODELO", "large-v3")
PYTHON_MINIMO = (3, 10)
VENV = Path.home() / ".transcritor" / "venv"
VENV_PYTHON = VENV / "Scripts" / "python.exe" if os.name == "nt" else VENV / "bin" / "python"
PASTA_BASE = Path(os.path.expanduser(os.environ.get("TRANSCRITOR_PASTA") or "~/Transcricoes"))
PASTAS = ("Entrada", "Finalizados", "Corrompidos", "Duplicados")

# Repositório no Hugging Face de onde o faster-whisper baixa cada modelo, e o tamanho
# aproximado do download em GB.
MODELOS = {
    "tiny": ("Systran/faster-whisper-tiny", 0.1),
    "base": ("Systran/faster-whisper-base", 0.2),
    "small": ("Systran/faster-whisper-small", 0.5),
    "medium": ("Systran/faster-whisper-medium", 1.5),
    "large-v2": ("Systran/faster-whisper-large-v2", 3.1),
    "large-v3": ("Systran/faster-whisper-large-v3", 3.1),
}

INSTALAR = {
    "python": {
        "Windows": [
            "winget install -e --id Python.Python.3.12",
            "(sem o winget, baixe em https://www.python.org/downloads/ e marque"
            " \"Add python.exe to PATH\" na primeira tela da instalacao)",
        ],
        "Darwin": [
            "instale o Homebrew pelo site https://brew.sh (o usuario faz isso, porque pede a senha do Mac)",
            "brew install python@3.12",
        ],
        "Linux": [
            "sudo apt install python3 python3-venv python3-pip"
            "   (Ubuntu e Debian; o usuario roda, porque pede a senha)",
        ],
    },
    "ffmpeg": {
        "Windows": ["winget install -e --id Gyan.FFmpeg"],
        "Darwin": ["brew install ffmpeg"],
        "Linux": ["sudo apt install ffmpeg   (Ubuntu e Debian; o usuario roda, porque pede a senha)"],
    },
}


def ok(texto):
    print("[ok] " + texto)


def aviso(texto):
    print("[aviso] " + texto)


def faltou(texto, comandos=None):
    print("[falta] " + texto)
    for linha in comandos or []:
        print("    " + linha)


def rodar(cmd):
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=120)
        return r.returncode, (r.stdout or "").strip()
    except Exception:
        return 1, ""


def python_com_faster_whisper():
    """Devolve (caminho, versão do Python, versão do faster-whisper) do primeiro Python
    que importa o faster-whisper, olhando antes o ambiente virtual da skill."""
    candidatos = []
    if VENV_PYTHON.exists():
        candidatos.append(str(VENV_PYTHON))
    candidatos.append(sys.executable)
    codigo = ("import sys, faster_whisper; "
              "print('%d.%d' % sys.version_info[:2], getattr(faster_whisper, '__version__', '?'))")
    for py in candidatos:
        ret, saida = rodar([py, "-c", codigo])
        partes = saida.split()
        if ret == 0 and len(partes) == 2:
            return py, partes[0], partes[1]
    return None, None, None


def achar_ffmpeg():
    achado = shutil.which("ffmpeg")
    if achado:
        return achado
    local = os.environ.get("LOCALAPPDATA")
    if local:
        base = os.path.join(local, "Microsoft", "WinGet", "Packages",
                            "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe")
        for cand in sorted(glob.glob(os.path.join(base, "ffmpeg-*-full_build", "bin", "ffmpeg.exe")),
                           reverse=True):
            return cand
    for cand in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if os.path.exists(cand):
            return cand
    return None


def achar_ffprobe(ffmpeg):
    pasta = os.path.dirname(ffmpeg)
    for nome in ("ffprobe.exe", "ffprobe"):
        if os.path.exists(os.path.join(pasta, nome)):
            return os.path.join(pasta, nome)
    return shutil.which("ffprobe")


def pasta_cache_hf():
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]) / "hub"
    if os.environ.get("XDG_CACHE_HOME"):
        return Path(os.environ["XDG_CACHE_HOME"]) / "huggingface" / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def modelo_baixado():
    """True ou False quando dá para conferir, None quando o modelo é desconhecido."""
    if os.path.isdir(MODELO):
        return os.path.exists(os.path.join(MODELO, "model.bin"))
    repo = MODELOS.get(MODELO, (None, None))[0]
    if not repo:
        return None
    pasta = pasta_cache_hf() / ("models--" + repo.replace("/", "--"))
    return any(pasta.glob("snapshots/*/model.bin"))


def espaco_livre_gb(caminho):
    alvo = Path(caminho)
    while not alvo.exists() and alvo != alvo.parent:
        alvo = alvo.parent
    try:
        return shutil.disk_usage(str(alvo)).free / 1e9
    except Exception:
        return None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    nome_sistema = {"Darwin": "macOS"}.get(SISTEMA, SISTEMA)
    print("Conferencia da skill transcricao, sistema %s" % nome_sistema)
    print()
    falta = False

    # Python. Vale a versão do Python que tem o faster-whisper e, sem ele, a deste.
    py_fw, ver_py_fw, ver_fw = python_com_faster_whisper()
    if py_fw:
        ver_py = tuple(int(x) for x in ver_py_fw.split("."))
        caminho_py = py_fw
    else:
        ver_py = sys.version_info[:2]
        caminho_py = sys.executable
    python_ok = ver_py >= PYTHON_MINIMO
    if python_ok:
        ok("Python %d.%d em %s" % (ver_py[0], ver_py[1], caminho_py))
    else:
        faltou("Python 3.10 ou mais novo, que roda os scripts da skill (este e o %d.%d)" % ver_py,
               INSTALAR["python"].get(SISTEMA))
        falta = True

    # ffmpeg e ffprobe, que vêm juntos.
    ffmpeg = achar_ffmpeg()
    ffprobe = achar_ffprobe(ffmpeg) if ffmpeg else None
    if ffmpeg and ffprobe:
        ok("ffmpeg e ffprobe em %s" % os.path.dirname(ffmpeg))
    else:
        faltou("ffmpeg, que abre o audio e o video, mede o volume e tira os frames",
               INSTALAR["ffmpeg"].get(SISTEMA))
        falta = True

    # faster-whisper, num ambiente virtual próprio.
    if py_fw:
        ok("faster-whisper %s" % ver_fw)
    elif not python_ok:
        faltou("faster-whisper, que transcreve a fala no proprio computador. Instale depois do Python.")
        falta = True
    else:
        comandos = [
            '"%s" -m venv "%s"' % (sys.executable, VENV),
            '"%s" -m pip install faster-whisper' % VENV_PYTHON,
        ]
        if SISTEMA == "Windows":
            comandos.append("(no PowerShell, comece cada linha com & antes do caminho entre aspas)")
        faltou("faster-whisper, que transcreve a fala no proprio computador. Ele vai num"
               " ambiente virtual em %s, separado do Python do sistema" % VENV, comandos)
        falta = True

    # Modelo do Whisper, que baixa sozinho na primeira transcrição.
    tamanho = MODELOS.get(MODELO, (None, None))[1]
    baixado = modelo_baixado()
    if baixado:
        ok("modelo %s ja baixado" % MODELO)
    elif baixado is None:
        aviso("modelo %s: nao deu para conferir se ele ja foi baixado" % MODELO)
    else:
        texto_tamanho = "perto de %.1f GB" % tamanho if tamanho else "tamanho desconhecido"
        aviso("o modelo %s ainda nao foi baixado. Ele baixa sozinho na primeira transcricao,"
              " %s, e precisa de internet nessa hora" % (MODELO, texto_tamanho))
        livre = espaco_livre_gb(pasta_cache_hf())
        if livre is not None and tamanho and livre < tamanho + 2:
            faltou("espaco em disco. Sobram %.1f GB, e o modelo pede %.1f GB mais uns 2 GB de folga"
                   % (livre, tamanho))
            falta = True

    # Pasta-base das gravações.
    if PASTA_BASE.is_dir():
        faltando = [p for p in PASTAS if not (PASTA_BASE / p).is_dir()]
        if faltando:
            aviso("a pasta-base %s existe, mas faltam as pastas %s" % (PASTA_BASE, ", ".join(faltando)))
        else:
            ok("pasta-base %s com as quatro pastas" % PASTA_BASE)
    else:
        aviso("a pasta-base %s ainda nao existe. A skill pergunta onde ficam as gravacoes"
              " antes de criar qualquer pasta" % PASTA_BASE)

    # GPU é opcional, e só entra no relatório quando existe.
    if shutil.which("nvidia-smi"):
        aviso("ha uma GPU NVIDIA. Para usar, defina WHISPER_DEVICE=cuda; o faster-whisper"
              " pede as bibliotecas da NVIDIA listadas em https://github.com/SYSTRAN/faster-whisper")

    print()
    print("PYTHON=%s" % (py_fw or ""))
    print("AMBIENTE_OK=%d" % (0 if falta else 1))
    sys.exit(1 if falta else 0)


if __name__ == "__main__":
    main()
