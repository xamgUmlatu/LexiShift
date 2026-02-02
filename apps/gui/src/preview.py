from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter

from lexishift_core import Match, PracticeGate, Replacer, VocabDataset, build_vocab_pool_from_dataset


@dataclass(frozen=True)
class ReplacementSpan:
    start: int
    end: int
    match: Match


class PreviewWorker(QThread):
    previewReady = Signal(int, str, object)

    def __init__(
        self,
        job_id: int,
        dataset: VocabDataset,
        text: str,
        practice_gate: Optional[PracticeGate] = None,
    ) -> None:
        super().__init__()
        self._job_id = job_id
        self._dataset = dataset
        self._text = text
        self._practice_gate = practice_gate

    def run(self) -> None:
        pool = build_vocab_pool_from_dataset(self._dataset, practice_gate=self._practice_gate)
        replacer = Replacer(pool)
        output, spans = apply_replacements_with_spans(replacer, self._text)
        self.previewReady.emit(self._job_id, output, spans)


class PreviewController(QObject):
    previewReady = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self._job_id = 0
        self._workers: List[PreviewWorker] = []

    def request(self, dataset: VocabDataset, text: str, *, practice_gate: Optional[PracticeGate] = None) -> None:
        self._job_id += 1
        worker = PreviewWorker(self._job_id, dataset, text, practice_gate=practice_gate)
        worker.previewReady.connect(self._handle_preview)
        worker.finished.connect(lambda: self._cleanup(worker))
        self._workers.append(worker)
        worker.start()

    def _handle_preview(self, job_id: int, output: str, spans: Sequence[ReplacementSpan]) -> None:
        if job_id != self._job_id:
            return
        self.previewReady.emit(output, spans)

    def _cleanup(self, worker: PreviewWorker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)


class ReplacementHighlighter(QSyntaxHighlighter):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._spans: Sequence[ReplacementSpan] = []
        self._format = QTextCharFormat()
        self._format.setBackground(QColor("#FFF2B2"))

    def set_spans(self, spans: Sequence[ReplacementSpan]) -> None:
        self._spans = spans
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        block_start = self.currentBlock().position()
        block_end = block_start + len(text)
        for span in self._spans:
            if span.end <= block_start or span.start >= block_end:
                continue
            start = max(span.start, block_start) - block_start
            end = min(span.end, block_end) - block_start
            self.setFormat(start, end - start, self._format)


def apply_replacements_with_spans(replacer: Replacer, text: str):
    result = replacer.replace_text(text, with_stats=True)
    tokens = replacer._pool.tokenizer.tokenize(text)
    word_positions = [idx for idx, token in enumerate(tokens) if token.kind == "word"]
    word_texts = [tokens[idx].text for idx in word_positions]
    return _apply_matches_with_spans(tokens, word_positions, word_texts, result.matches)


def _apply_matches_with_spans(tokens, word_positions, word_texts, matches: Iterable[Match]):
    output_parts: List[str] = []
    spans: List[ReplacementSpan] = []
    token_cursor = 0
    output_cursor = 0
    for match in matches:
        start_token_idx = word_positions[match.start_word_index]
        end_token_idx = word_positions[match.end_word_index]

        for token in tokens[token_cursor:start_token_idx]:
            output_parts.append(token.text)
            output_cursor += len(token.text)

        source_words = word_texts[match.start_word_index : match.end_word_index + 1]
        replacement_text = _apply_case(match.rule.replacement, source_words, match.rule.case_policy)
        start = output_cursor
        output_parts.append(replacement_text)
        output_cursor += len(replacement_text)
        spans.append(ReplacementSpan(start=start, end=output_cursor, match=match))

        token_cursor = end_token_idx + 1

    for token in tokens[token_cursor:]:
        output_parts.append(token.text)
        output_cursor += len(token.text)

    return "".join(output_parts), spans


def _apply_case(replacement: str, source_words: Sequence[str], policy: str) -> str:
    if policy == "as-is":
        return replacement
    if policy == "lower":
        return replacement.lower()
    if policy == "upper":
        return replacement.upper()
    if policy == "title":
        return replacement.title()
    if policy == "match":
        source_text = " ".join(source_words)
        if source_text.isupper():
            return replacement.upper()
        if source_words and source_words[0][:1].isupper():
            return replacement.title()
    return replacement
