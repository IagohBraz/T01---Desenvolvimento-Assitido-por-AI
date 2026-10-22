"""Indexa os PDFs de docs/ no Chroma.

Uso:
  .venv\\Scripts\\python scripts\\ingest.py --dry-run   # só extrai e quebra; sem API externa
  .venv\\Scripts\\python scripts\\ingest.py             # gera embeddings (OpenAI) e grava no Chroma
  .venv\\Scripts\\python scripts\\ingest.py --rebuild   # apaga a coleção e reindexa tudo

O relatório e a prévia dos chunks ficam em data/ (fora do versionamento).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xperiun_rag.config import load_settings  # noqa: E402
from xperiun_rag.ingest import IngestReport, ingest, load_chunks  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="não chama a OpenAI nem grava no Chroma")
    parser.add_argument("--rebuild", action="store_true", help="apaga a coleção antes de indexar")
    args = parser.parse_args()

    settings = load_settings()
    out_dir = settings.chroma_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        results, chunks_by_source = load_chunks(settings)
        report = IngestReport(documents=results)
        with (out_dir / "chunks_preview.jsonl").open("w", encoding="utf-8") as f:
            for chunks in chunks_by_source.values():
                for c in chunks:
                    f.write(json.dumps({"id": c.id, "text": c.page_content, **c.metadata}, ensure_ascii=False) + "\n")
    else:
        if "OPENAI_API_KEY" in settings.missing_keys():
            print("ERRO: OPENAI_API_KEY ausente no .env")
            return 2
        try:
            report = ingest(settings, rebuild=args.rebuild)
        except Exception as exc:  # erro do provedor/rede: mensagem curta, sem segredos
            print(f"ERRO na ingestão: {exc.__class__.__name__}: {str(exc)[:300]}")
            return 1

    (out_dir / "ingest_report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Modo: {'dry-run (sem API)' if args.dry_run else 'ingestão real'}")
    print(f"chunk_size={settings.chunk_size} chunk_overlap={settings.chunk_overlap} modelo={settings.embedding_model}")
    for d in report.documents:
        extra = f" | avisos: {'; '.join(d.warnings)}" if d.warnings else ""
        extra += f" | erro: {d.error}" if d.error else ""
        print(f"  [{d.status}] {d.source}: {d.pages} pág., {d.chunks} chunks, classificação: {d.classification or '-'}{extra}")
    for source in report.removed_sources:
        print(f"  [removido] {source}")
    if report.total_chunks_in_store is not None:
        print(f"Total de chunks no Chroma: {report.total_chunks_in_store}")
    print("OK" if report.ok else "CONCLUÍDO COM ERROS")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
