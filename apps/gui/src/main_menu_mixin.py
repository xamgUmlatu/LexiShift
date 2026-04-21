from __future__ import annotations

import sys

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMessageBox, QStyle

from helper_installer import (
    HELPER_STATE_CONFIGURED,
    HELPER_STATE_NEEDS_REPAIR,
)
from helper_ui import helper_connection_overall_state, manage_browser_connections
from i18n import t
from main_help import open_setup_guide
from main_paths import _app_data_dir, _startup_log_paths
from utils_paths import reveal_path


class MainWindowMenuMixin:
    def _setup_actions(self) -> None:
        self._open_action = QAction(t("menu.open_ruleset"), self)
        self._open_action.triggered.connect(self._open_dataset)

        self._save_action = QAction(t("menu.save_ruleset"), self)
        self._save_action.triggered.connect(self._save_dataset)

        self._save_as_action = QAction(t("menu.save_ruleset_as"), self)
        self._save_as_action.triggered.connect(self._save_dataset_as)

        self._settings_action = QAction(t("menu.settings"), self)
        self._settings_action.setMenuRole(QAction.PreferencesRole)
        self._settings_action.triggered.connect(self._open_settings)

        self._manage_profiles_action = QAction(t("menu.manage_profiles"), self)
        self._manage_profiles_action.triggered.connect(self._manage_profiles)

        self._manage_rulesets_action = QAction(t("menu.manage_rulesets"), self)
        self._manage_rulesets_action.triggered.connect(self._manage_rulesets)

        self._save_profiles_action = QAction(t("menu.save_profiles"), self)
        self._save_profiles_action.triggered.connect(self._save_profiles)

        self._add_rule_action = QAction(t("menu.add_rule"), self)
        self._add_rule_action.triggered.connect(self._add_rule)

        self._bulk_add_action = QAction(t("menu.bulk_add"), self)
        self._bulk_add_action.triggered.connect(self._bulk_add_rules)

        self._delete_rule_action = QAction(t("menu.delete_rule"), self)
        self._delete_rule_action.triggered.connect(self._delete_rule)

        self._edit_metadata_action = QAction(t("menu.edit_metadata"), self)
        self._edit_metadata_action.triggered.connect(self._edit_rule_metadata)

        self._install_helper_action = QAction(t("menu.manage_browser_connections"), self)
        self._install_helper_action.setMenuRole(QAction.ApplicationSpecificRole)
        self._install_helper_action.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self._install_helper_action.triggered.connect(self._manage_browser_connections)

        self._startup_diagnostics_action = QAction(t("menu.startup_diagnostics"), self)
        self._startup_diagnostics_action.triggered.connect(self._show_startup_diagnostics)

        self._open_log_dir_action = QAction(t("menu.open_log_directory"), self)
        self._open_log_dir_action.triggered.connect(self._open_log_directory)

        self._open_setup_guide_action = QAction(t("menu.open_setup_guide"), self)
        self._open_setup_guide_action.triggered.connect(self._open_setup_guide)

        self._export_json_action = QAction(t("menu.export_ruleset_json"), self)
        self._export_json_action.triggered.connect(self._export_json)

        self._export_code_action = QAction(t("menu.export_ruleset_code"), self)
        self._export_code_action.triggered.connect(self._export_code)

        self._export_profiles_json_action = QAction(t("menu.export_profiles_json"), self)
        self._export_profiles_json_action.triggered.connect(self._export_profiles_json)

        self._export_profiles_code_action = QAction(t("menu.export_profiles_code"), self)
        self._export_profiles_code_action.triggered.connect(self._export_profiles_code)

        self._import_json_action = QAction(t("menu.import_ruleset_json"), self)
        self._import_json_action.triggered.connect(self._import_json)

        self._import_code_action = QAction(t("menu.import_ruleset_code"), self)
        self._import_code_action.triggered.connect(self._import_code)

        self._import_profiles_json_action = QAction(t("menu.import_profiles_json"), self)
        self._import_profiles_json_action.triggered.connect(self._import_profiles_json)

        self._import_profiles_code_action = QAction(t("menu.import_profiles_code"), self)
        self._import_profiles_code_action.triggered.connect(self._import_profiles_code)

        self._save_action.setEnabled(False)
        self._update_rule_actions()
        self._apply_import_export_settings()

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()

        app_menu = menu_bar.addMenu(t("menu.app"))
        app_menu.addAction(self._install_helper_action)

        file_menu = menu_bar.addMenu(t("menu.file"))
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)

        import_menu = file_menu.addMenu(t("menu.import"))
        import_menu.addAction(self._import_json_action)
        import_menu.addAction(self._import_code_action)
        import_menu.addSeparator()
        import_menu.addAction(self._import_profiles_json_action)
        import_menu.addAction(self._import_profiles_code_action)

        export_menu = file_menu.addMenu(t("menu.export"))
        export_menu.addAction(self._export_json_action)
        export_menu.addAction(self._export_code_action)
        export_menu.addSeparator()
        export_menu.addAction(self._export_profiles_json_action)
        export_menu.addAction(self._export_profiles_code_action)

        file_menu.addSeparator()
        file_menu.addAction(self._settings_action)
        file_menu.addSeparator()

        self._quit_action = QAction(t("menu.quit"), self)
        self._quit_action.setMenuRole(QAction.QuitRole)
        self._quit_action.triggered.connect(self.close)
        file_menu.addAction(self._quit_action)

        profiles_menu = menu_bar.addMenu(t("menu.profiles"))
        profiles_menu.addAction(self._manage_profiles_action)
        profiles_menu.addAction(self._manage_rulesets_action)
        profiles_menu.addAction(self._save_profiles_action)
        profiles_menu.addSeparator()

        self._profiles_menu = profiles_menu
        self._profiles_action_group = QActionGroup(self)
        self._profiles_action_group.setExclusive(True)
        self._profile_actions: list[QAction] = []
        self._rebuild_profiles_menu()

        edit_menu = menu_bar.addMenu(t("menu.edit"))
        edit_menu.addAction(self._add_rule_action)
        edit_menu.addAction(self._bulk_add_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._edit_metadata_action)
        edit_menu.addAction(self._delete_rule_action)

        debug_menu = menu_bar.addMenu(t("menu.debug"))
        debug_menu.addAction(self._startup_diagnostics_action)
        debug_menu.addAction(self._open_log_dir_action)

        help_menu = menu_bar.addMenu(t("menu.help"))
        help_menu.addAction(self._open_setup_guide_action)

    def _refresh_helper_menu_label(self) -> None:
        state = helper_connection_overall_state(self._ui_settings)
        if state == HELPER_STATE_NEEDS_REPAIR:
            self._install_helper_action.setText(t("menu.repair_browser_connections"))
            return
        if state == HELPER_STATE_CONFIGURED:
            self._install_helper_action.setText(t("menu.manage_browser_connections"))
            return
        self._install_helper_action.setText(t("menu.install_helper"))

    def _manage_browser_connections(self) -> None:
        manage_browser_connections(self, self._ui_settings)
        self._refresh_helper_menu_label()

    def _open_log_directory(self) -> None:
        reveal_path(str(_app_data_dir()))

    def _open_setup_guide(self) -> None:
        open_setup_guide()

    def _show_startup_diagnostics(self) -> None:
        log_paths = _startup_log_paths()
        helper_log = _app_data_dir() / "helper_install.log"
        helper_tray_log = _app_data_dir() / "helper_tray.log"
        info = [
            t("dialogs.startup_diagnostics.app_data_location", path=str(_app_data_dir())),
            t("dialogs.startup_diagnostics.executable", path=str(sys.executable)),
            t("dialogs.startup_diagnostics.frozen", value=getattr(sys, "frozen", False)),
            t("dialogs.startup_diagnostics.meipass", value=getattr(sys, "_MEIPASS", None)),
            t("dialogs.startup_diagnostics.startup_log_paths"),
        ]
        for path in log_paths:
            info.append(
                t(
                    "dialogs.startup_diagnostics.startup_log_entry",
                    path=str(path),
                    exists=path.exists(),
                )
            )
        info.append(
            t(
                "dialogs.startup_diagnostics.helper_install_log",
                path=str(helper_log),
                exists=helper_log.exists(),
            )
        )
        info.append(
            t(
                "dialogs.startup_diagnostics.helper_tray_log",
                path=str(helper_tray_log),
                exists=helper_tray_log.exists(),
            )
        )
        info.append(t("dialogs.startup_diagnostics.hint"))
        QMessageBox.information(
            self,
            t("dialogs.startup_diagnostics.title"),
            "\n".join(info),
        )

    def _rebuild_profiles_menu(self) -> None:
        if not hasattr(self, "_profiles_menu"):
            return
        for action in self._profile_actions:
            self._profiles_menu.removeAction(action)
            self._profiles_action_group.removeAction(action)
        self._profile_actions = []

        settings = self.state.settings
        active_id = settings.active_profile_id
        for profile in settings.profiles:
            label = profile.name or profile.profile_id
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(profile.profile_id == active_id)
            action.triggered.connect(
                lambda checked, p=profile: self._switch_profile_from_menu(p, checked)
            )
            self._profiles_action_group.addAction(action)
            self._profiles_menu.addAction(action)
            self._profile_actions.append(action)

    def _switch_profile_from_menu(self, profile, checked: bool) -> None:
        if not checked:
            return
        if not self._confirm_discard_changes():
            self._rebuild_profiles_menu()
            return
        self._load_profile(profile)
