from __future__ import annotations

from dataclasses import replace
from typing import Optional

from PySide6.QtCore import QAbstractListModel, QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QFont

from vocab_replacer import Profile, VocabRule


class ProfilesListModel(QAbstractListModel):
    def __init__(
        self,
        profiles: Optional[tuple[Profile, ...]] = None,
        active_profile_id: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._profiles = profiles or tuple()
        self._active_profile_id = active_profile_id

    def set_profiles(self, profiles: tuple[Profile, ...]) -> None:
        self.beginResetModel()
        self._profiles = profiles
        self.endResetModel()

    def set_active_profile_id(self, active_profile_id: Optional[str]) -> None:
        self._active_profile_id = active_profile_id
        if not self._profiles:
            return
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._profiles) - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.FontRole, Qt.ForegroundRole])

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._profiles)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        profile = self._profiles[index.row()]
        is_active = profile.profile_id == self._active_profile_id
        if role in (Qt.DisplayRole, Qt.EditRole):
            name = profile.name or profile.profile_id
            return f"{name} (Active)" if is_active else name
        if role == Qt.UserRole:
            return profile
        if role == Qt.ToolTipRole:
            return profile.dataset_path
        if role == Qt.FontRole and is_active:
            font = QFont()
            font.setBold(True)
            return font
        if role == Qt.ForegroundRole and not profile.enabled:
            return QColor("#888888")
        return None


class RulesTableModel(QAbstractTableModel):
    rulesChanged = Signal(object)

    COLUMN_ENABLED = 0
    COLUMN_SOURCE = 1
    COLUMN_REPLACEMENT = 2
    COLUMN_PRIORITY = 3
    COLUMN_TAGS = 4
    COLUMN_DELETE = 5

    def __init__(self, rules: Optional[list[VocabRule]] = None) -> None:
        super().__init__()
        self._rules = rules or []

    def set_rules(self, rules: list[VocabRule]) -> None:
        self.beginResetModel()
        self._rules = rules
        self.endResetModel()

    def rules(self) -> list[VocabRule]:
        return list(self._rules)

    def rule_at(self, row: int) -> Optional[VocabRule]:
        if row < 0 or row >= len(self._rules):
            return None
        return self._rules[row]

    def add_rule(self, rule: Optional[VocabRule] = None) -> None:
        if rule is None:
            rule = VocabRule(source_phrase="", replacement="")
        row = len(self._rules)
        self.beginInsertRows(QModelIndex(), row, row)
        self._rules.append(rule)
        self.endInsertRows()
        self.rulesChanged.emit(self.rules())

    def remove_rule(self, row: int) -> None:
        if row < 0 or row >= len(self._rules):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self._rules.pop(row)
        self.endRemoveRows()
        self.rulesChanged.emit(self.rules())

    def update_rule(self, row: int, rule: VocabRule) -> None:
        if row < 0 or row >= len(self._rules):
            return
        self._rules[row] = rule
        top_left = self.index(row, 0)
        bottom_right = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)
        self.rulesChanged.emit(self.rules())

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rules)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else 6

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        return {
            self.COLUMN_ENABLED: "Enabled",
            self.COLUMN_SOURCE: "Source",
            self.COLUMN_REPLACEMENT: "Replacement",
            self.COLUMN_PRIORITY: "Priority",
            self.COLUMN_TAGS: "Tags",
            self.COLUMN_DELETE: "Delete",
        }.get(section)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        rule = self._rules[index.row()]
        column = index.column()
        if column == self.COLUMN_ENABLED and role == Qt.CheckStateRole:
            return Qt.Checked if rule.enabled else Qt.Unchecked
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == self.COLUMN_ENABLED:
                return "Yes" if rule.enabled else "No"
            if column == self.COLUMN_SOURCE:
                return rule.source_phrase
            if column == self.COLUMN_REPLACEMENT:
                return rule.replacement
            if column == self.COLUMN_PRIORITY:
                return str(rule.priority)
            if column == self.COLUMN_TAGS:
                return ", ".join(rule.tags)
            if column == self.COLUMN_DELETE:
                return "Delete"
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == self.COLUMN_ENABLED:
            return flags | Qt.ItemIsUserCheckable
        if index.column() == self.COLUMN_DELETE:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid():
            return False
        row = index.row()
        rule = self._rules[row]
        column = index.column()

        if column == self.COLUMN_ENABLED and role == Qt.CheckStateRole:
            updated = replace(rule, enabled=value == Qt.Checked)
        elif role in (Qt.EditRole, Qt.DisplayRole):
            if column == self.COLUMN_SOURCE:
                updated = replace(rule, source_phrase=str(value))
            elif column == self.COLUMN_REPLACEMENT:
                updated = replace(rule, replacement=str(value))
            elif column == self.COLUMN_PRIORITY:
                try:
                    priority = int(value)
                except (TypeError, ValueError):
                    priority = rule.priority
                updated = replace(rule, priority=priority)
            elif column == self.COLUMN_TAGS:
                tags = tuple(tag.strip() for tag in str(value).split(",") if tag.strip())
                updated = replace(rule, tags=tags)
            else:
                return False
        else:
            return False

        self._rules[row] = updated
        self.dataChanged.emit(index, index, [role])
        self.rulesChanged.emit(self.rules())
        return True

    def add_rules(self, rules: list[VocabRule]) -> None:
        if not rules:
            return
        start = len(self._rules)
        end = start + len(rules) - 1
        self.beginInsertRows(QModelIndex(), start, end)
        self._rules.extend(rules)
        self.endInsertRows()
        self.rulesChanged.emit(self.rules())
