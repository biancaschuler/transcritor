"""
Pré-processamento da skill transcricao.

Para uma mídia de entrada, gera ao lado dela:
  - <arquivo>.audio.wav          áudio mono 16 kHz, intermediário
  - <arquivo>.transcript.txt     transcrição bruta com timestamps, em UTF-8
  - <arquivo>.frames/            só em vídeo, um frame a cada 15 minutos (frame_HHhMMmSSs.jpg)

Uso:
    python transcrever.py "<pasta-base>/Entrada/<arquivo>"

Quem decide o tipo é o próprio arquivo. Com faixa de vídeo o script tira frames, e
sem ela (mensagem de voz em .mp4, .webm só de áudio, .m4a com capa) não tira. O tipo
aparece no stdout como tipo=video ou tipo=audio e entra no cabeçalho do
.transcript.txt.

A skill lê estes marcadores no stdout: tipo=, transcript=, frames_dir=, audio=,
AUDIO_MUDO=1, SILENCIO_10MIN= e ERRO_FFMPEG=1. As mensagens ficam em ASCII porque o
console do Windows nem sempre está em UTF-8.

Variáveis de ambiente, todas opcionais:
  WHISPER_MODELO               modelo do faster-whisper, padrão large-v3
  WHISPER_COMPUTE              precisão, padrão int8
  WHISPER_DEVICE               cpu ou cuda, padrão cpu
  WHISPER_THREADS              threads de CPU, padrão é o menor entre 8 e os núcleos lógicos
  WHISPER_BEAM                 beam size, padrão 1
  WHISPER_IDIOMA               código do idioma (pt, en, es...) ou auto, padrão pt
  WHISPER_CHUNK_THRESHOLD_MIN  acima de quantos minutos transcreve em blocos, padrão 60
  WHISPER_CHUNK_MIN            tamanho de cada bloco em minutos, padrão 30
  TRANSCRITOR_FRAMES_MIN       intervalo entre frames em minutos, padrão 15
  TRANSCRITOR_PASTA            pasta-base das gravações, padrão ~/Transcricoes
  TRANSCRITOR_GLOSSARIO        glossário de nomes próprios, padrão <pasta-base>/glossario.md

Sem o faster-whisper no Python que chamou o script, ele roda de novo com o Python do
ambiente virtual ~/.transcritor/venv, quando esse ambiente existe. O
verificar_ambiente.py mostra como criar o ambiente.

Código de saída. 0 deu certo, 1 o ffmpeg não abriu a mídia, 2 uso errado e 3 ambiente
(arquivo, ffmpeg ou faster-whisper faltando).
"""

# Deixa as anotações de tipo como texto, para o script abrir num Python mais velho e
# conseguir passar a vez para o Python do ambiente virtual.
from __future__ import annotations

import datetime
import glob
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ERRO_FFMPEG = 1
ERRO_USO = 2
ERRO_AMBIENTE = 3


def _caminho_env(nome: str, padrao: Path) -> Path:
    valor = os.environ.get(nome)
    return Path(os.path.expanduser(valor)) if valor else padrao


PASTA_BASE = _caminho_env("TRANSCRITOR_PASTA", Path.home() / "Transcricoes")
GLOSSARIO = _caminho_env("TRANSCRITOR_GLOSSARIO", PASTA_BASE / "glossario.md")
VENV_PYTHON = (Path.home() / ".transcritor" / "venv"
               / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))

# Modelo, precisão e idioma ficam num lugar só porque entram no cabeçalho do
# .transcript.txt. Meses depois, o cabeçalho diz de onde saiu cada arquivo, e a
# qualidade muda bastante entre o small e o large-v3.
#
# O padrão é o large-v3 porque, em reunião com muitos nomes próprios, o small erra
# grafia demais e a revisão consome o tempo que ele economiza. Para uma rodada
# rápida, use WHISPER_MODELO=small.
#
# Em processador com núcleos de eficiência (E-cores), usar todas as threads pode
# deixar a rodada mais lenta, porque os núcleos lentos atrasam o lote inteiro. Por
# isso o padrão para em 8, e WHISPER_THREADS muda o número.
MODELO = os.environ.get("WHISPER_MODELO", "large-v3")
COMPUTE = os.environ.get("WHISPER_COMPUTE", "int8")
DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
THREADS = int(os.environ.get("WHISPER_THREADS", str(min(8, os.cpu_count() or 8))))
BEAM = int(os.environ.get("WHISPER_BEAM", "1"))
IDIOMA = os.environ.get("WHISPER_IDIOMA", "pt").strip().lower()

FRAME_INTERVAL_SECONDS = int(os.environ.get("TRANSCRITOR_FRAMES_MIN", "15")) * 60

# Abaixo deste pico (dB) o áudio conta como mudo, só ruído de fundo ou silêncio
# digital. Serve para pegar cedo a gravação sem som, como uma captura de tela, e
# impedir que o Whisper entre em loop alucinando sobre o silêncio. Áudio normal de
# reunião tem max_volume perto de 0 dB.
SILENCE_MAX_DB = -50.0

# Janelas de silêncio longo dentro de um arquivo que tem som, o caso da reunião que
# acabou com a gravação ligada. Silêncio longo no fim corta a transcrição no fim do
# conteúdo real e evita o loop do Whisper ali.
SILENCE_NOISE_DB = -50.0      # piso de ruído do silencedetect, igual ao SILENCE_MAX_DB
SILENCE_MIN_SEC = 5 * 60      # só conta como silêncio longo a janela de 5 min ou mais
TRAILING_TOL_SEC = 2.0        # silêncio que termina a 2 s ou menos do fim é silêncio final
MIN_CONTENT_SEC = 10.0        # com menos que isso de conteúdo, o arquivo conta como mudo
SILENCE_REPORT_SEC = 10 * 60  # janela acima disso entra no resumo SILENCIO_10MIN=

# Arquivo acima de CHUNK_THRESHOLD_SEC é transcrito em blocos de CHUNK_SECONDS. O
# Whisper decodifica o áudio inteiro em memória de uma vez, perto de 64 KB/s, então
# um arquivo de 18 h passa de 4 GB de RAM. Cada bloco fechado vai para o .part e
# vira ponto de retomada, o que vale muito numa rodada de horas.
CHUNK_THRESHOLD_SEC = int(os.environ.get("WHISPER_CHUNK_THRESHOLD_MIN", "60")) * 60
CHUNK_SECONDS = int(os.environ.get("WHISPER_CHUNK_MIN", "30")) * 60

# Anti-loop sem descartar áudio. condition_on_previous_text=False impede que um
# contexto ruim ou repetido se propague para as janelas seguintes, e
# no_repeat_ngram_size=3 corta a repetição dentro de cada janela. O vad_filter fica
# de fora porque, em gravação com ganho baixo (pico perto de -10 dB), ele descarta
# fala real.
_WHISPER_KW = dict(
    language=None if IDIOMA == "auto" else IDIOMA,
    beam_size=BEAM,
    condition_on_previous_text=False,
    no_repeat_ngram_size=3,
)

# Abertura do initial_prompt montado com o glossário, na língua da gravação. Em
# idioma automático ou sem abertura conhecida, o prompt leva só a lista de termos,
# para não puxar a transcrição para outra língua.
_ABERTURA_PROMPT = {
    "pt": "Transcrição de reunião. Nomes próprios e termos: ",
    "en": "Meeting transcript. Proper names and terms: ",
    "es": "Transcripción de reunión. Nombres propios y términos: ",
}


def _preparar_log() -> logging.Logger:
    """Força UTF-8 no console e prepara o log em arquivo.

    O log vai para <pasta-base>/registro/transcricao_AAAA-MM-DD.log quando a
    pasta-base existe, para sobrar registro de uma rodada de horas que ninguém
    acompanhou. Ele não escreve no console, porque a skill lê os marcadores do
    stdout e nada pode sair duplicado ali."""
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    log = logging.getLogger("transcritor")
    log.setLevel(logging.INFO)
    log.propagate = False
    if log.handlers:
        return log
    if PASTA_BASE.is_dir():
        pasta = PASTA_BASE / "registro"
        pasta.mkdir(exist_ok=True)
        arquivo = pasta / f"transcricao_{datetime.date.today().isoformat()}.log"
        disco = logging.FileHandler(arquivo, encoding="utf-8")
        disco.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s",
                                             "%Y-%m-%d %H:%M:%S"))
        log.addHandler(disco)
    else:
        log.addHandler(logging.NullHandler())
    return log


LOG = _preparar_log()


def registrar(msg: str) -> None:
    """Imprime para quem está lendo agora e grava para quem for ler depois."""
    print(msg)
    LOG.info(msg)


def erro(msg: str, codigo: int) -> None:
    print(f"ERRO: {msg}", file=sys.stderr)
    LOG.error(msg)
    sys.exit(codigo)


def _ffmpeg_fallbacks() -> list[str]:
    """Lugares comuns do ffmpeg fora do PATH, usados só quando o shutil.which falha.
    No Windows é a pasta do winget (Gyan.FFmpeg) do usuário atual, com qualquer
    versão, e no macOS é o Homebrew."""
    candidatos = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        base = os.path.join(local, "Microsoft", "WinGet", "Packages",
                            "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe")
        candidatos += sorted(glob.glob(os.path.join(base, "ffmpeg-*-full_build", "bin", "ffmpeg.exe")),
                             reverse=True)
    candidatos += ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]
    return candidatos


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    for cand in _ffmpeg_fallbacks():
        if os.path.exists(cand):
            return cand
    erro("ffmpeg nao encontrado no PATH. Instale o ffmpeg e rode de novo.", ERRO_AMBIENTE)


def find_ffprobe(ffmpeg: str) -> str:
    pasta = Path(ffmpeg).parent
    for nome in ("ffprobe.exe", "ffprobe"):
        if (pasta / nome).exists():
            return str(pasta / nome)
    found = shutil.which("ffprobe")
    if found:
        return found
    erro("ffprobe nao encontrado junto do ffmpeg nem no PATH.", ERRO_AMBIENTE)


def rodar(cmd: list[str]) -> None:
    """Roda um comando do ffmpeg que precisa dar certo. Se ele falhar, o script mostra
    as últimas linhas do stderr, onde o ffmpeg diz o defeito (como "moov atom not
    found"), imprime ERRO_FFMPEG=1 e sai com código 1."""
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        for linha in (r.stderr or "").strip().splitlines()[-5:]:
            registrar(f"[ffmpeg] {linha}")
        print("ERRO_FFMPEG=1")
        erro(f"o ffmpeg falhou com codigo {r.returncode}", ERRO_FFMPEG)


def tem_faixa_de_video(ffprobe: str, midia: Path) -> bool | None:
    """True se o arquivo tem faixa de vídeo de verdade, False se não tem e None se o
    ffprobe não conseguiu ler. Capa de álbum embutida em mp3 e m4a aparece como faixa
    de vídeo com disposition attached_pic=1, e não conta."""
    try:
        r = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v",
             "-show_entries", "stream=codec_name:stream_disposition=attached_pic",
             "-of", "json", str(midia)],
            check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        faixas = json.loads(r.stdout or "{}").get("streams", [])
    except Exception:
        return None
    return any(not f.get("disposition", {}).get("attached_pic") for f in faixas)


def get_duration(ffprobe: str, media: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(media)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def measure_audio_level(ffmpeg: str, audio: Path) -> tuple[float | None, float | None]:
    """Roda o volumedetect do ffmpeg e devolve (mean_volume_db, max_volume_db), ou
    (None, None) se não der para medir. Nunca quebra o pipeline."""
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-nostats", "-i", str(audio),
             "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, errors="replace",
        )
        stderr = result.stderr or ""
        mean = max_ = None
        m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", stderr)
        if m:
            mean = float(m.group(1))
        m = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", stderr)
        if m:
            max_ = float(m.group(1))
        return mean, max_
    except Exception as exc:
        print(f"[audio] nivel nao medido (erro): {exc}")
        return None, None


def detect_long_silences(
    ffmpeg: str, audio: Path, total_dur: float,
    min_dur: float = SILENCE_MIN_SEC, noise_db: float = SILENCE_NOISE_DB,
) -> list[tuple[float, float]]:
    """Devolve as janelas (início, fim) de silêncio com min_dur segundos ou mais, pelo
    silencedetect do ffmpeg. Silêncio que vai até o fim do arquivo termina em
    total_dur. Em erro devolve lista vazia, e nunca quebra o pipeline."""
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-nostats", "-i", str(audio),
             "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"],
            capture_output=True, text=True, errors="replace",
        )
        stderr = result.stderr or ""
        starts = [float(x) for x in re.findall(r"silence_start:\s*(-?\d+(?:\.\d+)?)", stderr)]
        ends = [float(x) for x in re.findall(r"silence_end:\s*(-?\d+(?:\.\d+)?)", stderr)]
        intervals: list[tuple[float, float]] = []
        for i, s in enumerate(starts):
            e = ends[i] if i < len(ends) else total_dur
            intervals.append((max(0.0, s), e))
        return intervals
    except Exception as exc:
        print(f"[audio] silencedetect nao executado (erro): {exc}")
        return []


def extract_audio(ffmpeg: str, source: Path, audio_out: Path) -> None:
    if audio_out.exists():
        print(f"[audio] ja existe, pulando: {audio_out}")
        return
    print(f"[audio] extraindo audio mono 16kHz -> {audio_out}")
    rodar([ffmpeg, "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", str(audio_out)])


def _nome_frame(timestamp: float) -> str:
    hh, rem = divmod(int(timestamp), 3600)
    mm, ss = divmod(rem, 60)
    return f"frame_{hh:02d}h{mm:02d}m{ss:02d}s.jpg"


def _tirar_frame(ffmpeg: str, video: Path, timestamp: float, out_file: Path) -> None:
    rodar([ffmpeg, "-y", "-ss", str(timestamp), "-i", str(video),
           "-frames:v", "1", "-q:v", "2", "-strict", "unofficial", str(out_file)])


def extract_frames(
    ffmpeg: str, ffprobe: str, video: Path, frames_dir: Path,
    duration: float | None = None, silence_windows: list[tuple[float, float]] | None = None,
) -> None:
    """Tira um frame a cada FRAME_INTERVAL_SECONDS por seek pontual (-ss antes do -i),
    em vez de decodificar o vídeo inteiro num passe só com o filtro fps. Em vídeo
    longo isso é bem mais rápido, e permite pular o timestamp que cai numa janela de
    silêncio longo, onde não há fala para identificar.

    A duração deve vir do áudio extraído, que é mais confiável que o contêiner do
    vídeo. Sem ela, o script pergunta ao ffprobe do próprio vídeo."""
    if frames_dir.exists() and any(frames_dir.iterdir()):
        print(f"[frames] ja existem, pulando: {frames_dir}")
        return
    frames_dir.mkdir(parents=True, exist_ok=True)
    if duration is None:
        duration = get_duration(ffprobe, video)
    silence_windows = silence_windows or []

    if duration <= FRAME_INTERVAL_SECONDS:
        timestamp = duration / 2
        out_file = frames_dir / _nome_frame(timestamp)
        print(f"[frames] video curto ({duration:.0f}s), 1 frame em {timestamp:.0f}s -> {out_file}")
        _tirar_frame(ffmpeg, video, timestamp, out_file)
        return

    n_slots = int(duration // FRAME_INTERVAL_SECONDS) + 1
    print(f"[frames] extraindo ate {n_slots} frames (1 a cada {FRAME_INTERVAL_SECONDS}s) -> {frames_dir}")
    extracted = skipped = 0
    for idx in range(n_slots):
        timestamp = idx * FRAME_INTERVAL_SECONDS
        if timestamp >= duration:
            break
        if any(s <= timestamp <= e for s, e in silence_windows):
            skipped += 1
            continue
        _tirar_frame(ffmpeg, video, timestamp, frames_dir / _nome_frame(timestamp))
        extracted += 1
    print(f"[frames] concluido: {extracted} extraidos, {skipped} pulados (silencio longo)")


def load_glossary_prompt() -> str | None:
    """Monta o initial_prompt do Whisper com os termos confiáveis do glossário, para
    puxar a grafia certa de nome próprio. Entra só a linha de item marcada com ✅, e o
    nome em negrito dela. A linha com ❓ fica de fora para não espalhar grafia chutada.
    Devolve None sem glossário ou em erro, e nunca quebra a transcrição."""
    try:
        if not GLOSSARIO.exists():
            return None
        terms: list[str] = []
        seen: set[str] = set()
        for line in GLOSSARIO.read_text(encoding="utf-8-sig").splitlines():
            if not line.lstrip().startswith("- ") or "✅" not in line:
                continue
            m = re.search(r"\*\*(.+?)\*\*", line)
            if not m:
                continue
            term = m.group(1).strip()
            if term and term.lower() not in seen:
                seen.add(term.lower())
                terms.append(term)
        if not terms:
            return None
        prompt = _ABERTURA_PROMPT.get(IDIOMA, "") + ", ".join(terms) + "."
        # O initial_prompt tem orçamento curto, perto de 224 tokens. O corte respeita
        # a ordem do glossário, então o nome mais frequente vai no topo dele.
        max_chars = 900
        if len(prompt) > max_chars:
            prompt = prompt[:max_chars].rsplit(",", 1)[0] + "."
        return prompt
    except Exception as exc:
        print(f"[glossario] ignorado (erro ao ler): {exc}")
        return None


def parse_resume_point(part_file: Path) -> float:
    """Devolve, em segundos, o fim do último segmento gravado no .part, ou 0.0."""
    last_end = 0.0
    ts_pattern = re.compile(r"\[\d{2}:\d{2}:\d{2} -> (\d{2}:\d{2}:\d{2})\]")
    try:
        for line in part_file.read_text(encoding="utf-8").splitlines():
            m = ts_pattern.search(line)
            if m:
                h, mi, s = map(int, m.group(1).split(":"))
                last_end = h * 3600 + mi * 60 + s
    except Exception:
        pass
    return last_end


def trim_audio(ffmpeg: str, audio: Path, start_seconds: float, out: Path,
               length_seconds: float | None = None) -> None:
    """Cria um WAV mono 16 kHz a partir de start_seconds, com duração opcional."""
    cmd = [ffmpeg, "-y", "-ss", str(start_seconds)]
    if length_seconds is not None:
        cmd += ["-t", str(length_seconds)]
    cmd += ["-i", str(audio), "-ac", "1", "-ar", "16000", str(out)]
    rodar(cmd)


def format_ts(seconds: float) -> str:
    hh, rem = divmod(int(seconds), 3600)
    mm, ss = divmod(rem, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def cabecalho_modelo(tipo: str) -> str:
    """Linha de metadado que abre todo transcript, logo abaixo da duração e do idioma."""
    try:
        import faster_whisper
        versao = getattr(faster_whisper, "__version__", "?")
    except Exception:
        versao = "?"
    return (f"# modelo={MODELO} compute={COMPUTE} device={DEVICE} threads={THREADS} "
            f"beam={BEAM} faster_whisper={versao} "
            f"transcrito_em={datetime.date.today().isoformat()} tipo={tipo}\n")


def _write_segments(fh, segments, offset: float) -> None:
    """Grava os segmentos no .part com o deslocamento de tempo absoluto, com flush."""
    for seg in segments:
        fh.write(f"[{format_ts(seg.start + offset)} -> {format_ts(seg.end + offset)}] {seg.text.strip()}\n")
        fh.flush()


def transcribe(audio: Path, transcript_out: Path, ffmpeg: str, ffprobe: str, tipo: str) -> None:
    if transcript_out.exists():
        print(f"[transcricao] ja existe, pulando: {transcript_out}")
        return

    from faster_whisper import WhisperModel

    partial_out = Path(str(transcript_out) + ".part")
    resume_at = 0.0
    if partial_out.exists():
        resume_at = parse_resume_point(partial_out)
        if resume_at > 0:
            print(f"[transcricao] .part encontrado, retomando de {format_ts(resume_at)}")
        else:
            print("[transcricao] .part vazio ou sem segmentos, reiniciando do zero")

    registrar(f"[transcricao] carregando modelo '{MODELO}' ({COMPUTE}, {DEVICE}, {THREADS} threads)...")
    model = WhisperModel(MODELO, device=DEVICE, compute_type=COMPUTE, cpu_threads=THREADS)

    initial_prompt = load_glossary_prompt()
    if initial_prompt:
        print(f"[transcricao] priming do glossario com {initial_prompt.count(',') + 1} termos")

    try:
        total_dur = get_duration(ffprobe, audio)
    except Exception:
        total_dur = None

    if total_dur is not None and total_dur > CHUNK_THRESHOLD_SEC:
        _transcribe_chunked(model, audio, partial_out, transcript_out, ffmpeg,
                            resume_at, initial_prompt, total_dur, tipo)
    else:
        _transcribe_single(model, audio, partial_out, transcript_out, ffmpeg,
                           resume_at, initial_prompt, tipo)


def _transcribe_single(model, audio: Path, partial_out: Path, transcript_out: Path,
                       ffmpeg: str, resume_at: float, initial_prompt, tipo: str) -> None:
    trimmed = None
    audio_to_use = audio
    if resume_at > 0:
        trimmed = audio.with_suffix(".resume.wav")
        print(f"[transcricao] cortando audio a partir de {format_ts(resume_at)} ...")
        trim_audio(ffmpeg, audio, resume_at, trimmed)
        audio_to_use = trimmed

    print(f"[transcricao] transcrevendo {audio_to_use} ...")
    segments, info = model.transcribe(str(audio_to_use), initial_prompt=initial_prompt, **_WHISPER_KW)

    with open(partial_out, "a" if resume_at > 0 else "w", encoding="utf-8") as fh:
        if resume_at == 0:
            fh.write(f"# duration={info.duration:.1f}s language={info.language}\n")
            fh.write(cabecalho_modelo(tipo))
            fh.flush()
        _write_segments(fh, segments, resume_at)

    if trimmed and trimmed.exists():
        trimmed.unlink()

    os.replace(partial_out, transcript_out)
    registrar(f"[transcricao] concluido -> {transcript_out}")


def _transcribe_chunked(model, audio: Path, partial_out: Path, transcript_out: Path,
                        ffmpeg: str, resume_at: float, initial_prompt, total_dur: float,
                        tipo: str) -> None:
    """Transcreve um áudio longo em blocos de CHUNK_SECONDS a partir de resume_at. Cada
    bloco vira um WAV temporário, passa pelo modelo, vai para o .part com o tempo
    absoluto e o WAV do bloco sai em seguida."""
    n_total = int((total_dur + CHUNK_SECONDS - 1) // CHUNK_SECONDS)
    registrar(f"[transcricao] modo BLOCOS: {format_ts(total_dur)} em ~{n_total} blocos "
              f"de {CHUNK_SECONDS // 60} min (a partir de {format_ts(resume_at)})")

    # O bloco que cai inteiro numa janela de silêncio longo não passa pelo modelo. Isso
    # poupa CPU e evita alucinação em horas de sala vazia. Bloco de borda, com fala,
    # é transcrito normalmente.
    silences = detect_long_silences(ffmpeg, audio, total_dur)

    chunk_wav = Path(str(audio) + ".chunk.wav")
    with open(partial_out, "a" if resume_at > 0 else "w", encoding="utf-8") as fh:
        if resume_at == 0:
            fh.write(f"# duration={total_dur:.1f}s language={IDIOMA}\n")
            fh.write(cabecalho_modelo(tipo))
            fh.flush()
        start = resume_at
        while start < total_dur - 0.05:
            length = min(float(CHUNK_SECONDS), total_dur - start)
            end = start + length
            idx = int(start // CHUNK_SECONDS) + 1
            if any(s <= start + 0.5 and end <= e + 0.5 for s, e in silences):
                registrar(f"[transcricao] bloco {idx}/{n_total}: "
                          f"{format_ts(start)} -> {format_ts(end)}, SILENCIO, pulado")
                fh.write(f"[{format_ts(start)} -> {format_ts(end)}] [silencio longo nao transcrito]\n")
                fh.flush()
                start += length
                continue
            registrar(f"[transcricao] bloco {idx}/{n_total}: {format_ts(start)} -> {format_ts(end)} ...")
            trim_audio(ffmpeg, audio, start, chunk_wav, length_seconds=length)
            segments, _info = model.transcribe(str(chunk_wav), initial_prompt=initial_prompt, **_WHISPER_KW)
            _write_segments(fh, segments, start)
            if chunk_wav.exists():
                chunk_wav.unlink()
            start += length

    os.replace(partial_out, transcript_out)
    registrar(f"[transcricao] concluido (blocos) -> {transcript_out}")


def _fim_sem_transcricao(motivo: str, tipo: str, frames_dir: Path | None, audio_out: Path) -> None:
    print(f"[ALERTA] AUDIO MUDO/SILENCIOSO: {motivo}")
    print("[ALERTA] Transcricao PULADA para evitar o loop do Whisper em silencio.")
    if tipo == "video":
        print("[ALERTA] Analise pelo conteudo dos frames.")
    else:
        print("[ALERTA] O arquivo e so audio, entao nao ha frames para analisar.")
    registrar("[ok] pipeline concluido (SEM transcricao: audio mudo)")
    print("transcript=<NAO GERADO: audio mudo>")
    if frames_dir:
        print(f"frames_dir={frames_dir}")
    print(f"audio={audio_out}")
    print("AUDIO_MUDO=1")


def main() -> None:
    if len(sys.argv) != 2:
        erro("uso: python transcrever.py <caminho_da_midia>", ERRO_USO)

    midia = Path(sys.argv[1]).resolve()
    if not midia.exists():
        erro(f"arquivo nao encontrado: {midia}", ERRO_AMBIENTE)

    base = midia.with_suffix("")
    audio_out = Path(str(base) + ".audio.wav")
    transcript_out = Path(str(base) + ".transcript.txt")

    # Sem o faster-whisper aqui, passa a vez para o Python do ambiente virtual da skill.
    # Sem ambiente, falha cedo, antes de gastar minutos extraindo áudio e frames.
    if not transcript_out.exists() and importlib.util.find_spec("faster_whisper") is None:
        if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
            sys.stdout.flush()
            sys.exit(subprocess.run([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]).returncode)
        erro("faster-whisper nao instalado. Rode o verificar_ambiente.py, que mostra como instalar.",
             ERRO_AMBIENTE)

    registrar(f"[inicio] {midia}")
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe(ffmpeg)

    faixa = tem_faixa_de_video(ffprobe, midia)
    if faixa is None:
        registrar("[tipo] o ffprobe nao leu as faixas do arquivo, seguindo como audio")
    tipo = "video" if faixa else "audio"
    print(f"tipo={tipo}")
    frames_dir = Path(str(base) + ".frames") if tipo == "video" else None

    extract_audio(ffmpeg, midia, audio_out)

    # O nível e as janelas de silêncio saem antes dos frames. Gravação muda ainda
    # precisa de frames, que são a única fonte de conteúdo dela, mas o trecho de
    # silêncio longo num áudio com som não tem fala para identificar, e o frame dali
    # fica de fora.
    mean_db, max_db = measure_audio_level(ffmpeg, audio_out)
    if mean_db is not None or max_db is not None:
        registrar(f"[audio] nivel: mean={mean_db} dB | max={max_db} dB")
    is_mute = max_db is not None and max_db < SILENCE_MAX_DB

    try:
        total_dur = get_duration(ffprobe, audio_out)
    except Exception:
        total_dur = None

    silences: list[tuple[float, float]] = []
    if total_dur and not is_mute:
        silences = detect_long_silences(ffmpeg, audio_out, total_dur)

    if frames_dir:
        extract_frames(ffmpeg, ffprobe, midia, frames_dir, duration=total_dur,
                       silence_windows=None if is_mute else silences)

    if is_mute:
        _fim_sem_transcricao(f"max_volume={max_db} dB (< {SILENCE_MAX_DB} dB).", tipo, frames_dir, audio_out)
        return

    # O arquivo tem som. Silêncio longo no fim, o da reunião que acabou com a gravação
    # ligada, corta a transcrição no fim do conteúdo real. Silêncio longo no meio ou no
    # começo só aparece no relatório, para avaliar na análise.
    audio_for_transcribe = audio_out
    trimmed_content = Path(str(base) + ".audio.content.wav")
    content_end = None
    silences_10min: list[tuple[float, float]] = []
    if total_dur:
        for s, e in silences:
            if (e - s) >= SILENCE_REPORT_SEC:
                silences_10min.append((s, e))
            if e >= total_dur - TRAILING_TOL_SEC:
                print(f"[audio] silencio FINAL longo {format_ts(s)}-{format_ts(e)} "
                      f"({(e - s) / 60:.1f} min): transcrevendo so ate {format_ts(s)}")
                content_end = s if content_end is None else min(content_end, s)
            else:
                print(f"[audio] silencio longo NO MEIO {format_ts(s)}-{format_ts(e)} "
                      f"({(e - s) / 60:.1f} min): mantido, avaliar o periodo na analise")
    if silences_10min:
        janelas = "; ".join(f"{format_ts(s)}-{format_ts(e)} ({(e - s) / 60:.1f}min)"
                            for s, e in silences_10min)
        registrar(f"[audio] RESUMO silencios > 10 min: {len(silences_10min)} janela(s): {janelas}")
        print(f"SILENCIO_10MIN={janelas}")
    else:
        print("[audio] RESUMO silencios > 10 min: nenhum")

    if content_end is not None and content_end < MIN_CONTENT_SEC:
        _fim_sem_transcricao(f"conteudo audivel < {MIN_CONTENT_SEC:.0f}s.", tipo, frames_dir, audio_out)
        return

    if content_end is not None:
        if not trimmed_content.exists():
            print(f"[audio] cortando audio ate {format_ts(content_end)} (remove silencio final) ...")
            rodar([ffmpeg, "-y", "-t", str(content_end), "-i", str(audio_out), str(trimmed_content)])
        audio_for_transcribe = trimmed_content

    transcribe(audio_for_transcribe, transcript_out, ffmpeg, ffprobe, tipo)

    if content_end is not None and trimmed_content.exists():
        trimmed_content.unlink()  # intermediário derivado, o .audio.wav fica

    registrar("[ok] pipeline concluido")
    print(f"transcript={transcript_out}")
    if frames_dir:
        print(f"frames_dir={frames_dir}")
    print(f"audio={audio_out}")


if __name__ == "__main__":
    main()
