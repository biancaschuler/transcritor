#!/usr/bin/env python3
"""Extrai o tema de cada transcrição concluída, de áudio e de vídeo.

Para cada .md dentro de <pasta-base>/Finalizados, o script pega um tema curto,
preferindo o campo **Tema:** da seção "Informações gerais". Sem esse campo, usa o
primeiro parágrafo da seção "Resumo objetivo".

Cada gravação tem uma subpasta em Finalizados, e a mídia de app de conversa tem uma
subpasta por conversa, com vários .md dentro. O rglob dá conta dos dois casos. O tipo
sai do tipo= que o cabeçalho do anexo bruto traz e, sem ele, da pasta <nome>.frames
ao lado do .md. Sem nenhum dos dois, o item conta como áudio.

A leitura é sempre em UTF-8, para evitar o mojibake do Windows PowerShell 5.1, que lê
arquivo como ANSI.

O agrupamento por tema fica de fora de propósito. Agrupar é julgamento, que o modelo
faz melhor lendo esta saída, e o script só garante a extração.

Uso:
  python extrair_temas.py            # saída em texto, pasta padrão
  python extrair_temas.py --json     # saída em JSON, uma lista de itens
  python extrair_temas.py --bases "<pasta>" "<outra pasta>"

A pasta padrão é <TRANSCRITOR_PASTA>/Finalizados, ou ~/Transcricoes/Finalizados
quando a variável não existe.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path


def pasta_padrao() -> str:
    base = os.environ.get("TRANSCRITOR_PASTA") or "~/Transcricoes"
    return str(Path(os.path.expanduser(base)) / "Finalizados")


def extrair_tema(texto: str) -> str:
    """Devolve o tema mais conciso que o arquivo tiver."""
    # 1) Campo **Tema:** de "Informações gerais", o mais curto e direto.
    m = re.search(r"\*\*Tema:\*\*\s*(.+)", texto)
    if m:
        return m.group(1).strip()

    # 2) Primeiro parágrafo não vazio depois do título "Resumo objetivo".
    m = re.search(r"^#{1,6}\s*Resumo objetivo\s*$", texto, re.MULTILINE)
    if m:
        for linha in texto[m.end():].splitlines():
            t = linha.strip()
            if t:
                return t

    # 3) Último recurso, o primeiro parágrafo que não seja título.
    for linha in texto.splitlines():
        t = linha.strip()
        if t and not t.startswith("#"):
            return t

    return "(sem tema identificado)"


def tipo_do_arquivo(md: Path, texto: str) -> str:
    """vídeo quando o anexo bruto diz tipo=video ou quando há frames ao lado do .md."""
    if re.search(r"\btipo=video\b", texto):
        return "vídeo"
    if re.search(r"\btipo=audio\b", texto):
        return "áudio"
    # x_1.md e x_2.md, de várias reuniões na mesma gravação, dividem a pasta x.frames.
    nomes = {md.stem, re.sub(r"_\d+$", "", md.stem)}
    if any((md.parent / f"{nome}.frames").is_dir() for nome in nomes):
        return "vídeo"
    return "áudio"


def coletar(bases):
    itens = []
    for base in bases:
        p = Path(base)
        if not p.exists():
            print(f"[aviso] pasta nao encontrada: {p}", file=sys.stderr)
            continue
        for md in sorted(p.rglob("*.md")):
            # utf-8-sig tira o BOM que o Bloco de Notas e o PowerShell gravam no começo
            # do arquivo. Com ele, o título da primeira linha não casa com o ^#.
            texto = md.read_text(encoding="utf-8-sig", errors="replace")
            itens.append({
                "tipo": tipo_do_arquivo(md, texto),
                "pasta": md.parent.name,
                "arquivo": str(md),
                "tema": extrair_tema(texto),
            })
    return itens


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bases", nargs="*",
                    help="Pastas a varrer, no lugar da pasta padrão.")
    ap.add_argument("--json", action="store_true", help="Saída em JSON.")
    args = ap.parse_args()

    # Garante UTF-8 na saída do console do Windows.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    itens = coletar(args.bases or [pasta_padrao()])

    if args.json:
        print(json.dumps(itens, ensure_ascii=False, indent=2))
        return

    por_tipo = {}
    for it in itens:
        por_tipo.setdefault(it["tipo"], []).append(it)

    print(f"# {len(itens)} transcrições concluídas\n")
    for tipo, lst in por_tipo.items():
        print(f"## {tipo.capitalize()} ({len(lst)})\n")
        for it in lst:
            print(f"### {it['pasta']}")
            print(it["tema"])
            print()


if __name__ == "__main__":
    main()
