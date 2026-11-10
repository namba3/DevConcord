"""Conservative, reviewable issue archive manager.

Supports record-only Markdown tables. A complex issue (detail heading, unsafe
reference, unknown column shape) is intentionally rejected for manual review.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import unquote, urlsplit

try:
    from . import validate_docs
except ImportError:
    import validate_docs


TERMINAL = {"完了", "見送り", "done", "closed", "won't fix", "wont fix"}
STATUS_HEADERS = {"状態", "status"}
DATE_HEADERS = {"完了日", "closedat", "terminaldate"}
ARCHIVE_HEADING = "## 完了課題アーカイブ"


class ArchiveError(ValueError):
    pass


def _read(path: Path) -> str:
    if path.is_symlink():
        raise ArchiveError(f"symlink is not an editable register: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ArchiveError(f"cannot read {path}: {exc}") from exc


def _row(text: str, path: Path, issue_id: str):
    records = [x for x in validate_docs._issue_record_rows(text, path) if x.issue_id == issue_id]
    if len(records) != 1:
        raise ArchiveError(f"{issue_id}: expected one canonical row in {path}")
    lines = text.splitlines(keepends=True)
    index = records[0].line - 1
    cells = validate_docs._markdown_cells(lines[index])
    if cells is None:
        raise ArchiveError(f"{issue_id}: invalid row")
    for header in range(index - 2, -1, -1):
        heads = validate_docs._markdown_cells(lines[header])
        separator = validate_docs._markdown_cells(lines[header + 1]) if header + 1 < index else None
        if heads is None or separator is None or len(heads) != len(cells):
            continue
        if not all(re.fullmatch(r":?-+:?", x.replace(" ", "")) for x in separator):
            continue
        keys = [validate_docs._header_key(x) for x in heads]
        if "id" in keys or "issueid" in keys:
            return index, lines[header], lines[header + 1], lines[index], keys, cells
    raise ArchiveError(f"{issue_id}: no table header found")


def _active_paths(main: Path, managed_dir: Path | None) -> list[Path]:
    if managed_dir is None:
        return [main]
    if not managed_dir.is_dir() or managed_dir.is_symlink():
        raise ArchiveError("managed directory is missing or a symlink")
    text = _read(main)
    section = re.search(r"(?ms)^## (?:サブ課題表|Subregisters)[^\n]*\n(.*?)(?=^## |\Z)", text)
    if not section:
        raise ArchiveError("federated index has no subregister section")
    paths = []
    for dest in re.findall(r"\[[^\]]+\]\(([^)]+)\)", section.group(1)):
        parsed = urlsplit(dest)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        path = (main.parent / unquote(parsed.path)).resolve()
        if not path.is_relative_to(managed_dir.resolve()) or not path.is_file():
            raise ArchiveError(f"out-of-scope or missing subregister: {dest}")
        if path in paths:
            raise ArchiveError(f"repeated subregister: {dest}")
        paths.append(path)
    if not paths:
        raise ArchiveError("no indexed subregisters")
    return paths


def _indexed_archives(main: Path, archive_dir: Path) -> list[Path]:
    text = _read(main)
    match = re.search(r"(?ms)^## 完了課題アーカイブ[^\n]*\n(.*?)(?=^## |\Z)", text)
    if not match:
        return []
    result = []
    fenced = False
    for line in match.group(1).splitlines():
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        link = re.match(r"^\s*-\s*\[[^\]]+\]\(([^)]+)\)\s*$", line)
        if not link:
            continue
        dest = link.group(1)
        parsed = urlsplit(dest)
        if parsed.scheme or parsed.netloc or not parsed.path:
            raise ArchiveError("invalid archive link")
        path = (main.parent / unquote(parsed.path)).resolve()
        if not path.is_relative_to(archive_dir.resolve()) or not path.is_file() or path.is_symlink():
            raise ArchiveError(f"unavailable indexed archive: {dest}")
        if path in result:
            raise ArchiveError(f"duplicate archive link: {dest}")
        result.append(path)
    return result


def _validate(main: Path, managed: Path | None, archive: Path | None) -> None:
    if managed is None:
        errors = validate_docs.validate_single_issue_register(main, archive)
    else:
        errors = validate_docs.validate_federated_issue_register(main, managed, archive)
    if errors:
        raise ArchiveError("register validation failed:\n" + "\n".join(errors[:12]))


def _safe_scope(main: Path, archive: Path) -> None:
    root = main.parent.resolve()
    target = archive.resolve()
    if target == root or not target.is_relative_to(root):
        raise ArchiveError("archive directory must be inside active index directory")
    for p in (main, archive):
        if p.is_symlink():
            raise ArchiveError(f"symlink scope is forbidden: {p}")
    for p in archive.parents:
        if p == root:
            break
        if p.is_symlink():
            raise ArchiveError(f"symlink archive parent is forbidden: {p}")


def _ensure_simple(text: str, path: Path, issue_id: str) -> None:
    if re.search(r"(?m)^#{1,6}\s+" + re.escape(issue_id) + r"(?:\b|$)", text):
        raise ArchiveError(f"{issue_id}: detailed heading requires manual reviewed migration: {path}")
    if re.search(r"\[" + re.escape(issue_id.casefold()) + r"\]\(", text.casefold()):
        raise ArchiveError(f"{issue_id}: linked ISS reference requires manual review: {path}")
    if re.search(r"\]\([^)\n]*#" + re.escape(issue_id.casefold()) + r"(?:\b|[-)])", text.casefold()):
        raise ArchiveError(f"{issue_id}: anchored reference requires manual review: {path}")


def _source_marker(source: Path, main: Path) -> str:
    try:
        return source.relative_to(main.parent.resolve()).as_posix()
    except ValueError as exc:
        raise ArchiveError("source must be inside active index directory") from exc


def _archive_file(directory: Path) -> Path:
    year = date.today().year
    part = 1
    while True:
        suffix = "" if part == 1 else f"-part{part}"
        path = directory / f"closed-{year}{suffix}.md"
        if not path.exists() or path.stat().st_size < 256 * 1024:
            return path
        part += 1


def _archive_block(issue_id: str, source: str, header: str, separator: str, row: str) -> str:
    return (
        f"\n## {issue_id}\n"
        f"<!-- devconcord-issue-source: {source} -->\n\n"
        + header.rstrip("\n") + "\n" + separator.rstrip("\n") + "\n"
        + row.rstrip("\n") + "\n"
    )


def _replace_index(text: str, main: Path, archive: Path) -> str:
    link = archive.relative_to(main.parent.resolve()).as_posix()
    match_section = re.search(r"(?ms)^## 完了課題アーカイブ[^\n]*\n(.*?)(?=^## |\Z)", text)
    if match_section:
        fenced = False
        for line in match_section.group(1).splitlines():
            if re.match(r"^\s*(`{3,}|~{3,})", line):
                fenced = not fenced
                continue
            if not fenced and re.match(r"^\s*-\s*\[[^\]]+\]\(" + re.escape(link) + r"\)\s*$", line):
                return text
    new_line = f"- [終端ISS {archive.stem}]({link})\n"
    match = re.search(r"(?m)^## 完了課題アーカイブ[^\n]*\n", text)
    if match:
        return text[:match.end()] + new_line + text[match.end():]
    return text.rstrip("\n") + "\n\n" + ARCHIVE_HEADING + "\n\n" + new_line


def _archive_block_from_text(text: str, issue_id: str):
    pattern = re.compile(r"(?ms)^## " + re.escape(issue_id) + r"\s*\n(.*?)(?=^## |\Z)")
    match = pattern.search(text)
    if not match:
        raise ArchiveError(f"{issue_id}: missing canonical archive block")
    marker = re.search(r"(?m)^<!-- devconcord-issue-source: ([^\n<>]+) -->$", match.group(1))
    if not marker:
        raise ArchiveError(f"{issue_id}: missing source provenance")
    return match, marker.group(1)


def _write_transaction(changes: dict[Path, tuple[str | None, str | None]]) -> None:
    """Use one advisory lock, CAS-like checks, and best-effort rollback.

    Filesystem multi-file atomicity is not guaranteed; check before and after.
    """
    if not changes:
        return
    root = min((p.parent for p in changes), key=lambda p: len(p.parts))
    lock = root / ".devconcord-issue-archive.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ArchiveError(f"another archive operation holds {lock}") from exc
    os.close(fd)
    completed: list[Path] = []
    try:
        for path, (old, new) in changes.items():
            actual = _read(path) if path.exists() else None
            if actual != old:
                raise ArchiveError(f"concurrent edit detected: {path}")
            if path.is_symlink():
                raise ArchiveError(f"symlink destination: {path}")
        for path, (_old, new) in changes.items():
            if new is None:
                path.unlink(missing_ok=True)
                completed.append(path)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(prefix=".devconcord-", dir=path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                    stream.write(new)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp_name, path)
                completed.append(path)
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
    except Exception:
        for path in reversed(completed):
            old = changes[path][0]
            try:
                if old is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(old, encoding="utf-8")
            except OSError:
                pass
        raise
    finally:
        lock.unlink(missing_ok=True)


def manage(args: argparse.Namespace) -> list[str]:
    main = (args.issue_register or args.issue_main).resolve()
    managed = args.managed_dir.resolve() if args.managed_dir else None
    archive_dir = args.archive_dir.absolute()
    _safe_scope(main, archive_dir)
    if archive_dir.exists() and not archive_dir.is_dir():
        raise ArchiveError("archive scope is not a directory")
    _validate(main, managed, archive_dir if archive_dir.exists() or _indexed_archives(main, archive_dir) else None)
    if args.mode == "inspect":
        return [f"validated active index {main} and indexed Archive"]

    sources = _active_paths(main, managed)
    original = {p: _read(p) for p in [main, *sources, *_indexed_archives(main, archive_dir)]}
    texts = original.copy()
    all_active = {}
    terminal_count = 0
    for source in sources:
        for record in validate_docs._issue_record_rows(texts[source], source):
            if record.issue_id in all_active:
                raise ArchiveError("duplicate active ISS")
            all_active[record.issue_id] = source
            _, _, _, _, keys, cells = _row(texts[source], source, record.issue_id)
            status_col = next((i for i, key in enumerate(keys) if key in STATUS_HEADERS), None)
            if status_col is not None and cells[status_col].strip().casefold() in TERMINAL:
                terminal_count += 1

    ids = list(dict.fromkeys(args.ids or []))
    if args.mode == "archive":
        if args.auto:
            if terminal_count < args.min_closed_count:
                return [f"no batch: {terminal_count} terminal Active records (< {args.min_closed_count})"]
            cutoff = date.today() - timedelta(days=args.min_age_days)
            ids = []
            for issue_id, source in all_active.items():
                _, _, _, _, keys, cells = _row(texts[source], source, issue_id)
                status_col = next((i for i, key in enumerate(keys) if key in STATUS_HEADERS), None)
                date_col = next((i for i, key in enumerate(keys) if key in DATE_HEADERS), None)
                if status_col is None or date_col is None or cells[status_col].strip().casefold() not in TERMINAL:
                    continue
                try:
                    closed = date.fromisoformat(cells[date_col].strip())
                except ValueError:
                    continue
                if closed <= cutoff:
                    ids.append(issue_id)
        if not ids:
            return ["no eligible ISS selected"]
        dest = _archive_file(archive_dir).resolve()
        if dest not in texts:
            texts[dest] = "# 完了・見送りISS Archive\n"
            original[dest] = None
        for issue_id in ids:
            if issue_id not in all_active:
                raise ArchiveError(f"{issue_id}: not found in Active")
            source = all_active[issue_id]
            if source == main and managed:
                raise ArchiveError("main index may not contain canonical ISS")
            _ensure_simple(texts[source], source, issue_id)
            _ensure_simple(texts[main], main, issue_id)
            idx, head, sep, row, keys, cells = _row(texts[source], source, issue_id)
            status_col = next((i for i, key in enumerate(keys) if key in STATUS_HEADERS), None)
            if status_col is None or cells[status_col].strip().casefold() not in TERMINAL:
                raise ArchiveError(f"{issue_id}: terminal status column required")
            acceptance_keys = {"完了条件", "acceptance", "acceptancecriteria"}
            evidence_keys = {"根拠", "根拠・検証", "根拠・適用する検証", "evidence", "verification"}
            acceptance = next((cells[i].strip() for i, key in enumerate(keys) if key in acceptance_keys), "")
            evidence = next((cells[i].strip() for i, key in enumerate(keys) if key in evidence_keys), "")
            if acceptance in {"", "—", "-"} or evidence in {"", "—", "-"}:
                raise ArchiveError(f"{issue_id}: completion criteria and evidence are required")
            if issue_id in [r.issue_id for r in validate_docs._issue_record_rows(texts[dest], dest)]:
                raise ArchiveError(f"{issue_id}: already archived")
            lines = texts[source].splitlines(keepends=True)
            del lines[idx]
            texts[source] = "".join(lines)
            texts[dest] += _archive_block(issue_id, _source_marker(source, main), head, sep, row)
        texts[main] = _replace_index(texts[main], main, dest)
    else:
        if not ids:
            raise ArchiveError("restore requires --ids")
        archives = _indexed_archives(main, archive_dir)
        for issue_id in ids:
            if issue_id in all_active:
                raise ArchiveError(f"{issue_id}: already exists in Active")
            found = [(p, _archive_block_from_text(texts[p], issue_id)) for p in archives if re.search(r"(?m)^## " + re.escape(issue_id) + r"\s*$", texts[p])]
            if len(found) != 1:
                raise ArchiveError(f"{issue_id}: expected one indexed archive record")
            path, (match, marker) = found[0]
            source = (main.parent / marker).resolve()
            if source not in sources:
                raise ArchiveError(f"{issue_id}: source no longer indexed")
            idx, header, sep, row, keys, cells = _row(texts[path], path, issue_id)
            if re.search(r"(?m)^#{1,6}\s+" + re.escape(issue_id) + r"\b", texts[source]):
                raise ArchiveError(f"{issue_id}: active detail heading collision")
            target_lines = texts[source].splitlines(keepends=True)
            header_index = next((i for i, line in enumerate(target_lines[:-1]) if line.rstrip() == header.rstrip() and target_lines[i + 1].rstrip() == sep.rstrip()), None)
            if header_index is None:
                raise ArchiveError(f"{issue_id}: original table schema no longer exists")
            insert_at = header_index + 2
            while insert_at < len(target_lines) and target_lines[insert_at].lstrip().startswith("|"):
                insert_at += 1
            if not args.reason or not args.reason.strip():
                raise ArchiveError("restore requires --reason")
            if "\n" in args.reason or "\r" in args.reason:
                raise ArchiveError("reason must be a single line")
            status_col = next((i for i, key in enumerate(keys) if key in STATUS_HEADERS), None)
            if status_col is None:
                raise ArchiveError("restored issue must have a status column")
            previous_status = cells[status_col].strip()
            cells[status_col] = args.reopen_status
            target_lines.insert(insert_at, "| " + " | ".join(cells) + " |\n")
            texts[source] = "".join(target_lines)
            texts[source] += (
                f"\n### {issue_id} 再オープン記録\n"
                f"- 旧状態: {previous_status}\n"
                f"- 理由: {args.reason.strip()}\n"
                f"- 元Archive: {path.name}\n"
            )
            texts[path] = texts[path][:match.start()] + texts[path][match.end():]
    changed = {p: (original.get(p), text) for p, text in texts.items() if original.get(p) != text}
    if args.apply:
        _write_transaction(changed)
        try:
            _validate(main, managed, archive_dir)
        except Exception as error:
            reverse = {p: (new, old) for p, (old, new) in changed.items()}
            try:
                _write_transaction(reverse)
            except Exception as rollback_error:
                raise ArchiveError(f"validation failed and rollback incomplete: {rollback_error}") from rollback_error
            raise ArchiveError(f"validation failed; original files restored: {error}") from error
    return [f"{'applied' if args.apply else 'dry-run'}: {args.mode}: {', '.join(ids)}", *[f"{p}: {'create' if before is None else 'update'}" for p, (before, _new) in changed.items()]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "archive", "restore"))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--issue-register", type=Path)
    group.add_argument("--issue-main", type=Path)
    parser.add_argument("--managed-dir", type=Path)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--ids", nargs="+", metavar="ISS-####")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--min-closed-count", type=int, default=50)
    parser.add_argument("--min-age-days", type=int, default=30)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reason", help="reopening reason (required for restore)")
    parser.add_argument("--reopen-status", choices=("未着手", "レビュー待ち"), default="未着手")
    args = parser.parse_args(argv)
    if bool(args.issue_main) != bool(args.managed_dir):
        parser.error("--managed-dir is required only with --issue-main")
    if args.auto and (args.mode != "archive" or args.ids):
        parser.error("--auto only applies to archive without --ids")
    if args.mode == "archive" and not args.auto and not args.ids:
        parser.error("archive requires --auto or --ids")
    if args.min_age_days < 0 or args.min_closed_count < 1:
        parser.error("invalid batch thresholds")
    try:
        for line in manage(args):
            print(line)
    except (ArchiveError, OSError) as exc:
        print(f"Archive operation blocked: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
