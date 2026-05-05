#!/usr/bin/env python3
"""
Busca seguidores de perfis públicos do Instagram e estima alcance de stories.
Uso: python buscar_seguidores.py
     python buscar_seguidores.py --login seu_usuario  (mais estável com login)
"""

import argparse
import csv
import time
import sys
from datetime import datetime

try:
    import instaloader
except ImportError:
    print("Instalando instaloader...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "instaloader"])
    import instaloader

USERNAMES = [
    "eusoupedro_henrique",
    "arantesdanielly",
    "dranayaracastro",
    "dayanealho",
    "recameneses",
    "virginiasuassuna",
    "tiapriodonto",
    "camipiresveg",
    "reginabritomanicure",
    "dicasdealine_",
    "dercileneebm",
    "daysousapersonal",
    "marcosplinsken",
    "nannysaraiva",
    "gabriellem.personall",
    "annekarolynesena",
    "ma.duli",
    "dopaminasrun",
    "brunaalvesnutri",
    "vivianemelo_oo",
    "taticintra98",
    "alinesantosnut",
    "acatiamaria",
    "thainemarot",
    "receitasdoyan",
    "leilianealvesdealmeida",
    "tatianagarciabeautyacademy",
    "turibeiro",
    "correndocomraika",
    "mayracamelo",
    "camillaartiagavet",
    "val.acarvalho",
    "elianemartins7",
    "julianarhv",
    "eduardo.alves94",
    "smarilurdes",
    "vitoria_585",
    "_geovanna29",
    "camilacdferreira",
    "anapaulasouzatributario",
    "wandersontimao10",
    "melfranco2019",
    "waleriabertolucci",
    "letyciaaa.gomes",
    "danuzasou",
]


def estimar_alcance(seguidores: int) -> tuple[float, float]:
    """Retorna (alcance_min, alcance_max) estimado para um story."""
    if seguidores <= 10_000:
        return seguidores * 0.15, seguidores * 0.20
    elif seguidores <= 100_000:
        return seguidores * 0.10, seguidores * 0.15
    else:
        return seguidores * 0.05, seguidores * 0.10


def buscar_perfis(login: str | None = None, senha: str | None = None) -> list[dict]:
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    if login:
        try:
            if senha:
                L.login(login, senha)
            else:
                L.load_session_from_file(login)
            print(f"Sessão carregada para @{login}\n")
        except Exception as e:
            print(f"Aviso: não foi possível autenticar ({e}). Continuando sem login.\n")

    resultados = []

    for i, username in enumerate(USERNAMES, 1):
        print(f"[{i:02d}/{len(USERNAMES)}] Buscando @{username}...", end=" ", flush=True)
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            seguidores = profile.followers
            alcance_min, alcance_max = estimar_alcance(seguidores)
            status = "ok"
            print(f"{seguidores:,} seguidores | alcance estimado: {int(alcance_min):,}–{int(alcance_max):,}")
        except instaloader.exceptions.ProfileNotExistsException:
            seguidores, alcance_min, alcance_max = None, None, None
            status = "perfil_nao_encontrado"
            print("PERFIL NÃO ENCONTRADO")
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            seguidores, alcance_min, alcance_max = None, None, None
            status = "perfil_privado"
            print("PERFIL PRIVADO")
        except Exception as e:
            seguidores, alcance_min, alcance_max = None, None, None
            status = f"erro: {e}"
            print(f"ERRO — {e}")

        resultados.append({
            "username": username,
            "seguidores": seguidores,
            "alcance_min": int(alcance_min) if alcance_min else None,
            "alcance_max": int(alcance_max) if alcance_max else None,
            "status": status,
        })

        # Pausa para evitar rate-limit (aumentar se começar a bloquear)
        if i < len(USERNAMES):
            time.sleep(3)

    return resultados


def salvar_csv(resultados: list[dict], caminho: str) -> None:
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "seguidores", "alcance_min", "alcance_max", "status"])
        writer.writeheader()
        writer.writerows(resultados)


def imprimir_resumo(resultados: list[dict]) -> None:
    encontrados = [r for r in resultados if r["seguidores"] is not None]
    if not encontrados:
        print("\nNenhum dado obtido.")
        return

    total_seguidores = sum(r["seguidores"] for r in encontrados)
    total_alcance_min = sum(r["alcance_min"] for r in encontrados)
    total_alcance_max = sum(r["alcance_max"] for r in encontrados)
    media_seguidores = total_seguidores // len(encontrados)

    print("\n" + "=" * 55)
    print("RESUMO DO ALCANCE — STORIES DO EVENTO")
    print("=" * 55)
    print(f"Perfis analisados:       {len(encontrados)} de {len(USERNAMES)}")
    print(f"Total de seguidores:     {total_seguidores:,}")
    print(f"Média por perfil:        {media_seguidores:,} seguidores")
    print(f"Alcance estimado total:  {total_alcance_min:,} – {total_alcance_max:,} pessoas")
    print(f"(cada story visto por ≈ {total_alcance_min // len(encontrados):,}–{total_alcance_max // len(encontrados):,} pessoas em média)")
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(description="Busca seguidores no Instagram e estima alcance de stories")
    parser.add_argument("--login", help="Usuário do Instagram para autenticar (mais estável)")
    parser.add_argument("--senha", help="Senha (opcional; usa sessão salva se omitido)")
    parser.add_argument("--output", default="alcance_stories.csv", help="Nome do arquivo CSV de saída")
    args = parser.parse_args()

    print(f"Iniciando busca para {len(USERNAMES)} perfis...\n")
    resultados = buscar_perfis(login=args.login, senha=args.senha)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    nome_arquivo = args.output.replace(".csv", f"_{timestamp}.csv")
    salvar_csv(resultados, nome_arquivo)
    print(f"\nDados salvos em: {nome_arquivo}")

    imprimir_resumo(resultados)


if __name__ == "__main__":
    main()
