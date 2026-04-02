from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QDialog, QMessageBox

from dialogs_code import BulkRulesDialog
from i18n import t
from lexishift_core.helper.installed_packs import resolve_installed_pack_artifact
from lexishift_core import (
    RuleMetadata,
    SynonymGenerator,
    SynonymOptions,
    SynonymSourceSettings,
    SynonymSources,
    VocabRule,
)


def _resolve_translation_pack_path(
    raw_path: str | None,
    *,
    legacy_artifact_names: tuple[str, ...],
) -> str | None:
    path_text = str(raw_path or "").strip()
    if not path_text:
        return None
    path = Path(path_text)
    if not path.is_dir():
        return path_text
    resolved_artifact = resolve_installed_pack_artifact(path.parent, path.name)
    if resolved_artifact is not None:
        return str(resolved_artifact)
    for artifact_name in legacy_artifact_names:
        candidate = path / artifact_name
        if candidate.exists():
            return str(candidate)
    return path_text


class MainWindowBulkRulesMixin:
    def _bulk_add_rules(self) -> None:
        default_pack_ids = self._default_bulk_pack_ids()
        dialog = BulkRulesDialog(default_pack_ids=default_pack_ids, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        targets = dialog.targets()
        if not targets:
            return
        selected_pack_ids = dialog.selected_pack_ids()
        if not selected_pack_ids:
            QMessageBox.information(
                self,
                t("dialogs.bulk_add.title"),
                t("dialogs.bulk_add.select_dictionary"),
            )
            return
        self._remember_bulk_pack_selection(selected_pack_ids)
        self._append_log(t("logs.bulk_add_targets", count=len(targets)))
        rules = self._generate_synonym_rules(targets, selected_pack_ids=selected_pack_ids)
        if not rules:
            QMessageBox.information(
                self,
                t("dialogs.bulk_add.title"),
                t("dialogs.bulk_add.no_synonyms"),
            )
            return
        self.rules_model.add_rules(rules)

    def _default_bulk_pack_ids(self) -> set[str]:
        settings = self.state.settings.synonyms
        pack_ids: set[str] = set()
        if not settings:
            return pack_ids
        if settings.wordnet_dir:
            pack_ids.add("wordnet-en")
        if settings.moby_path:
            pack_ids.add("moby-en")
        if settings.last_selected_pack_ids:
            return set(settings.last_selected_pack_ids)
        language_packs = settings.language_packs or {}
        if language_packs.get("odenet-de"):
            pack_ids.add("odenet-de")
        elif language_packs.get("openthesaurus-de"):
            pack_ids.add("openthesaurus-de")
        if language_packs.get("jp-wordnet-sqlite"):
            pack_ids.add("jp-wordnet-sqlite")
        elif language_packs.get("jp-wordnet"):
            pack_ids.add("jp-wordnet")
        for pack_id in ("jmdict-ja-en", "freedict-de-en", "freedict-en-de", "cc-cedict-zh-en"):
            if language_packs.get(pack_id):
                pack_ids.add(pack_id)
        return pack_ids

    def _remember_bulk_pack_selection(self, selected_pack_ids: set[str]) -> None:
        settings = self.state.settings.synonyms or SynonymSourceSettings()
        updated = replace(settings, last_selected_pack_ids=tuple(sorted(selected_pack_ids)))
        self.state.update_settings(replace(self.state.settings, synonyms=updated))

    def _generate_synonym_rules(
        self,
        targets: list[str],
        *,
        selected_pack_ids: set[str] | None = None,
    ) -> list[VocabRule]:
        settings = self.state.settings.synonyms
        selected_pack_ids = set(selected_pack_ids or [])
        language_packs = settings.language_packs if settings else {}
        if not settings:
            QMessageBox.warning(
                self,
                t("dialogs.synonym_expansion.title"),
                t("dialogs.synonym_expansion.configure_sources"),
            )
            return []
        packs_by_pair: dict[str, set[str]] = {}
        for pack_id in selected_pack_ids:
            pair_key = self._pair_for_pack(pack_id)
            if not pair_key:
                continue
            packs_by_pair.setdefault(pair_key, set()).add(pack_id)
        openthesaurus_path = language_packs.get("openthesaurus-de") if language_packs else None
        odenet_path = language_packs.get("odenet-de") if language_packs else None
        jp_wordnet_path = language_packs.get("jp-wordnet") if language_packs else None
        jp_wordnet_sqlite_path = language_packs.get("jp-wordnet-sqlite") if language_packs else None
        jmdict_path = language_packs.get("jmdict-ja-en") if language_packs else None
        freedict_de_en_path = _resolve_translation_pack_path(
            language_packs.get("freedict-de-en") if language_packs else None,
            legacy_artifact_names=(
                "freedict-de-en.sqlite",
                "deu-eng.sqlite",
                "deu-eng.tei",
            ),
        )
        freedict_en_de_path = _resolve_translation_pack_path(
            language_packs.get("freedict-en-de") if language_packs else None,
            legacy_artifact_names=(
                "freedict-en-de.sqlite",
                "eng-deu.sqlite",
                "eng-deu.tei",
            ),
        )
        cc_cedict_path = language_packs.get("cc-cedict-zh-en") if language_packs else None
        if cc_cedict_path and Path(cc_cedict_path).is_dir():
            candidate = Path(cc_cedict_path) / "cedict_ts.u8"
            cc_cedict_path = str(candidate) if candidate.exists() else cc_cedict_path
        rules: list[VocabRule] = []
        seen_sources: set[str] = set()
        duplicate_count = 0
        for pair_key, pack_ids in sorted(packs_by_pair.items()):
            use_wordnet = "wordnet-en" in pack_ids
            use_moby = "moby-en" in pack_ids
            use_openthesaurus = "openthesaurus-de" in pack_ids
            use_odenet = "odenet-de" in pack_ids
            use_jp_wordnet = "jp-wordnet" in pack_ids
            use_jp_wordnet_sqlite = "jp-wordnet-sqlite" in pack_ids
            use_jmdict = "jmdict-ja-en" in pack_ids
            use_freedict_de_en = "freedict-de-en" in pack_ids
            use_freedict_en_de = "freedict-en-de" in pack_ids
            use_cc_cedict = "cc-cedict-zh-en" in pack_ids

            if not any(
                [
                    use_wordnet and settings.wordnet_dir,
                    use_moby and settings.moby_path,
                    use_openthesaurus and openthesaurus_path,
                    use_odenet and odenet_path,
                    use_jp_wordnet and jp_wordnet_path,
                    use_jp_wordnet_sqlite and jp_wordnet_sqlite_path,
                    use_jmdict and jmdict_path,
                    use_freedict_de_en and freedict_de_en_path,
                    use_freedict_en_de and freedict_en_de_path,
                    use_cc_cedict and cc_cedict_path,
                ]
            ):
                continue

            missing_sources = []
            if use_wordnet and settings.wordnet_dir and not Path(settings.wordnet_dir).exists():
                missing_sources.append(t("sources.wordnet_dir"))
            if use_moby and settings.moby_path and not Path(settings.moby_path).exists():
                missing_sources.append(t("sources.moby_file"))
            if use_openthesaurus and openthesaurus_path and not Path(openthesaurus_path).exists():
                missing_sources.append(t("sources.openthesaurus_file"))
            if use_odenet and odenet_path and not Path(odenet_path).exists():
                missing_sources.append(t("sources.odenet_file"))
            if use_jp_wordnet and jp_wordnet_path and not Path(jp_wordnet_path).exists():
                missing_sources.append(t("sources.jp_wordnet_file"))
            if (
                use_jp_wordnet_sqlite
                and jp_wordnet_sqlite_path
                and not Path(jp_wordnet_sqlite_path).exists()
            ):
                missing_sources.append(t("sources.jp_wordnet_sqlite_file"))
            if use_jmdict and jmdict_path and not Path(jmdict_path).exists():
                missing_sources.append(t("sources.jmdict_file"))
            if (
                use_freedict_de_en
                and freedict_de_en_path
                and not Path(freedict_de_en_path).exists()
            ):
                missing_sources.append(t("sources.freedict_de_en_file"))
            if (
                use_freedict_en_de
                and freedict_en_de_path
                and not Path(freedict_en_de_path).exists()
            ):
                missing_sources.append(t("sources.freedict_en_de_file"))
            if use_cc_cedict and cc_cedict_path and Path(cc_cedict_path).is_dir():
                missing_sources.append(t("sources.cc_cedict_file"))
            if use_cc_cedict and cc_cedict_path and not Path(cc_cedict_path).exists():
                missing_sources.append(t("sources.cc_cedict_file"))
            if missing_sources:
                QMessageBox.warning(
                    self,
                    t("dialogs.synonym_expansion.title"),
                    t(
                        "dialogs.synonym_expansion.missing_sources",
                        sources=", ".join(missing_sources),
                    ),
                )
                return []

            selected_labels = []
            label_map = {
                "wordnet-en": t("packs.wordnet"),
                "moby-en": t("packs.moby"),
                "openthesaurus-de": t("packs.openthesaurus"),
                "odenet-de": t("packs.odenet"),
                "jp-wordnet": t("packs.jp_wordnet"),
                "jp-wordnet-sqlite": t("packs.jp_wordnet_sqlite"),
                "jmdict-ja-en": t("packs.jmdict"),
                "freedict-de-en": t("packs.freedict_de_en"),
                "freedict-en-de": t("packs.freedict_en_de"),
                "cc-cedict-zh-en": t("packs.cc_cedict"),
            }
            for pack_id in pack_ids:
                selected_labels.append(label_map.get(pack_id, pack_id))
            if selected_labels:
                self._append_log(
                    t("logs.dictionaries", dictionaries=", ".join(sorted(selected_labels)))
                )

            cc_cedict_file = (
                Path(cc_cedict_path)
                if use_cc_cedict and cc_cedict_path and Path(cc_cedict_path).is_file()
                else None
            )
            sources = SynonymSources(
                wordnet_dir=Path(settings.wordnet_dir)
                if use_wordnet and settings.wordnet_dir
                else None,
                moby_path=Path(settings.moby_path) if use_moby and settings.moby_path else None,
                openthesaurus_path=Path(openthesaurus_path)
                if use_openthesaurus and openthesaurus_path
                else None,
                odenet_path=Path(odenet_path) if use_odenet and odenet_path else None,
                jp_wordnet_path=Path(jp_wordnet_path)
                if use_jp_wordnet and jp_wordnet_path
                else None,
                jp_wordnet_sqlite_path=(
                    Path(jp_wordnet_sqlite_path)
                    if use_jp_wordnet_sqlite and jp_wordnet_sqlite_path
                    else None
                ),
                jmdict_path=Path(jmdict_path) if use_jmdict and jmdict_path else None,
                freedict_de_en_path=(
                    Path(freedict_de_en_path)
                    if use_freedict_de_en and freedict_de_en_path
                    else None
                ),
                freedict_en_de_path=(
                    Path(freedict_en_de_path)
                    if use_freedict_en_de and freedict_en_de_path
                    else None
                ),
                cc_cedict_path=cc_cedict_file,
            )
            embedding_paths = self._embedding_paths_for_pair(settings, pair_key)
            options = SynonymOptions(
                max_synonyms=settings.max_synonyms,
                include_phrases=settings.include_phrases,
                lower_case=settings.lower_case,
                require_consensus=settings.require_consensus,
                use_embeddings=settings.use_embeddings,
                embedding_paths=embedding_paths,
                embedding_pair=pair_key,
                embedding_threshold=settings.embedding_threshold,
                embedding_fallback=settings.embedding_fallback,
            )
            generator = SynonymGenerator(sources, options=options)
            self._log_source_stats(pack_ids, generator.stats())
            if generator.total_entries() == 0:
                stats = generator.stats()
                QMessageBox.information(
                    self,
                    t("dialogs.synonym_expansion.title"),
                    t(
                        "dialogs.synonym_expansion.no_entries",
                        wordnet=stats.get("wordnet", 0),
                        moby=stats.get("moby", 0),
                        openthesaurus=stats.get("openthesaurus", 0),
                        odenet=stats.get("odenet", 0),
                        jp_wordnet=stats.get("jp_wordnet", 0),
                        jmdict=stats.get("jmdict", 0),
                        cc_cedict=stats.get("cc_cedict", 0),
                        freedict_de_en=stats.get("freedict_de_en", 0),
                        freedict_en_de=stats.get("freedict_en_de", 0),
                    ),
                )
                continue

            for target in targets:
                synonyms, used_fallback = generator.synonyms_for_detail(target)
                if not synonyms:
                    self._append_log(
                        t("logs.no_synonyms_for", target=target),
                        color=self._status_color("error"),
                    )
                    if settings and settings.use_embeddings and settings.embedding_fallback:
                        if not generator.has_embeddings():
                            self._append_log(t("logs.embeddings_not_loaded", target=target))
                        elif not generator.embeddings_support_neighbors():
                            self._append_log(t("logs.embeddings_no_neighbors"))
                        elif not generator.embeddings_has_vector(target):
                            self._append_log(t("logs.no_embedding_vector", target=target))
                        else:
                            self._append_log(t("logs.embeddings_zero_neighbors", target=target))
                else:
                    if used_fallback:
                        self._append_log(
                            t("logs.embeddings_fallback_count", target=target, count=len(synonyms))
                        )
                    else:
                        self._append_log(
                            t("logs.synonyms_found", target=target, count=len(synonyms))
                        )
                for synonym in synonyms:
                    if synonym in seen_sources:
                        duplicate_count += 1
                        tags = ("synonym", "conflict")
                        rules.append(
                            VocabRule(
                                source_phrase=synonym,
                                replacement=target,
                                enabled=False,
                                tags=tags,
                                metadata=RuleMetadata(language_pair=pair_key),
                            )
                        )
                        continue
                    seen_sources.add(synonym)
                    rules.append(
                        VocabRule(
                            source_phrase=synonym,
                            replacement=target,
                            tags=("synonym",),
                            metadata=RuleMetadata(language_pair=pair_key),
                        )
                    )
        if not rules and selected_pack_ids:
            QMessageBox.warning(
                self,
                t("dialogs.synonym_expansion.title"),
                t("dialogs.synonym_expansion.select_configured"),
            )
            return []
        if duplicate_count:
            message = t("dialogs.bulk_add.duplicates", count=duplicate_count)
            QMessageBox.information(self, t("dialogs.bulk_add.title"), message)
            self._append_log(message)
        return rules

    def _log_source_stats(self, selected_pack_ids: set[str], stats: dict[str, int]) -> None:
        if not selected_pack_ids:
            return
        settings = self.state.settings.synonyms or SynonymSourceSettings()
        language_packs = settings.language_packs or {}
        pack_to_stat = {
            "wordnet-en": "wordnet",
            "moby-en": "moby",
            "openthesaurus-de": "openthesaurus",
            "odenet-de": "odenet",
            "jp-wordnet": "jp_wordnet",
            "jp-wordnet-sqlite": "jp_wordnet",
            "jmdict-ja-en": "jmdict",
            "cc-cedict-zh-en": "cc_cedict",
            "freedict-de-en": "freedict_de_en",
            "freedict-en-de": "freedict_en_de",
        }
        pack_to_path = {
            "wordnet-en": settings.wordnet_dir,
            "moby-en": settings.moby_path,
            "openthesaurus-de": language_packs.get("openthesaurus-de"),
            "odenet-de": language_packs.get("odenet-de"),
            "jp-wordnet": language_packs.get("jp-wordnet"),
            "jp-wordnet-sqlite": language_packs.get("jp-wordnet-sqlite"),
            "jmdict-ja-en": language_packs.get("jmdict-ja-en"),
            "cc-cedict-zh-en": language_packs.get("cc-cedict-zh-en"),
            "freedict-de-en": _resolve_translation_pack_path(
                language_packs.get("freedict-de-en"),
                legacy_artifact_names=(
                    "freedict-de-en.sqlite",
                    "deu-eng.sqlite",
                    "deu-eng.tei",
                ),
            ),
            "freedict-en-de": _resolve_translation_pack_path(
                language_packs.get("freedict-en-de"),
                legacy_artifact_names=(
                    "freedict-en-de.sqlite",
                    "eng-deu.sqlite",
                    "eng-deu.tei",
                ),
            ),
        }
        label_map = {
            "wordnet-en": t("packs.wordnet"),
            "moby-en": t("packs.moby"),
            "openthesaurus-de": t("packs.openthesaurus"),
            "odenet-de": t("packs.odenet"),
            "jp-wordnet": t("packs.jp_wordnet"),
            "jp-wordnet-sqlite": t("packs.jp_wordnet_sqlite"),
            "jmdict-ja-en": t("packs.jmdict"),
            "cc-cedict-zh-en": t("packs.cc_cedict"),
            "freedict-de-en": t("packs.freedict_de_en"),
            "freedict-en-de": t("packs.freedict_en_de"),
        }
        for pack_id in sorted(selected_pack_ids):
            stat_key = pack_to_stat.get(pack_id)
            if not stat_key:
                continue
            count = stats.get(stat_key, 0)
            if count > 0:
                self._append_log(
                    t("logs.source_loaded", name=label_map.get(pack_id, pack_id), count=count)
                )
            else:
                path = pack_to_path.get(pack_id) or ""
                size = ""
                if path and Path(path).exists():
                    try:
                        size = str(Path(path).stat().st_size)
                    except OSError:
                        size = ""
                self._append_log(
                    t(
                        "logs.source_empty",
                        name=label_map.get(pack_id, pack_id),
                        path=path,
                        size=size,
                    ),
                    color=self._status_color("error"),
                )
                if pack_id == "odenet-de" and path:
                    probe = self._probe_odenet(path)
                    if probe:
                        self._append_log(
                            t(
                                "logs.odenet_probe",
                                entries=probe.get("entries", 0),
                                lemmas=probe.get("lemmas", 0),
                                senses=probe.get("senses", 0),
                            ),
                            color=self._status_color("error"),
                        )
                        if probe.get("parse_error"):
                            self._append_log(
                                t("logs.odenet_parse_error", error=probe.get("parse_error")),
                                color=self._status_color("error"),
                            )

    def _probe_odenet(self, path: str) -> dict[str, int]:
        from xml.etree import ElementTree

        try:
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return {}
        data: dict[str, int | str] = {
            "entries": text.count("LexicalEntry"),
            "lemmas": text.count("Lemma"),
            "senses": text.count("Sense"),
        }
        try:
            for _event, _elem in ElementTree.iterparse(path, events=("end",)):
                pass
        except ElementTree.ParseError as exc:
            data["parse_error"] = str(exc)
        return data

    def _pair_for_pack(self, pack_id: str) -> Optional[str]:
        if pack_id in {"wordnet-en", "moby-en"}:
            return "en-en"
        if pack_id in {"openthesaurus-de", "odenet-de"}:
            return "de-de"
        if pack_id in {"jp-wordnet", "jp-wordnet-sqlite"}:
            return "ja-ja"
        if pack_id == "freedict-de-en":
            return "en-de"
        if pack_id == "freedict-en-de":
            return "de-en"
        if pack_id == "jmdict-ja-en":
            return "en-ja"
        if pack_id == "cc-cedict-zh-en":
            return "en-zh"
        return None
