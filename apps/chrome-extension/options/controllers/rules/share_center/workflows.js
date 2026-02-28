(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createWorkflows(options) {
    const opts = options && typeof options === "object" ? options : {};
    const rulesShareController = opts.rulesShareController && typeof opts.rulesShareController === "object"
      ? opts.rulesShareController
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const shareCenterSelection = opts.shareCenterSelection && typeof opts.shareCenterSelection === "object"
      ? opts.shareCenterSelection
      : null;
    const isFullMode = typeof opts.isFullMode === "function" ? opts.isFullMode : (() => true);
    const getCurrentProfileId = typeof opts.getCurrentProfileId === "function"
      ? opts.getCurrentProfileId
      : (() => "default");
    const getSelectedLeafEntries = typeof opts.getSelectedLeafEntries === "function"
      ? opts.getSelectedLeafEntries
      : (() => []);
    const normalizePath = typeof opts.normalizePath === "function"
      ? opts.normalizePath
      : ((value) => String(value || "").trim());
    const resolveExportFileName = typeof opts.resolveExportFileName === "function"
      ? opts.resolveExportFileName
      : ((scope, profileId) => `lexishift-share-${scope}-${profileId}.json`);
    const formatByteSize = typeof opts.formatByteSize === "function"
      ? opts.formatByteSize
      : ((size) => `${Number(size) || 0} B`);
    const downloadJsonFile = typeof opts.downloadJsonFile === "function"
      ? opts.downloadJsonFile
      : ((content) => new Blob([content]).size);
    const setExportStatus = typeof opts.setExportStatus === "function" ? opts.setExportStatus : (() => {});
    const setImportStatus = typeof opts.setImportStatus === "function" ? opts.setImportStatus : (() => {});
    const updateSummary = typeof opts.updateSummary === "function" ? opts.updateSummary : (() => {});
    const syncForProfile = typeof opts.syncForProfile === "function" ? opts.syncForProfile : (() => Promise.resolve(null));
    const tr = typeof opts.tr === "function"
      ? opts.tr
      : ((key, fallback) => String(fallback || key || ""));
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { SUCCESS: "#3c5a2a", ERROR: "#b42318" };
    const importFileInput = opts.importFileInput || null;
    const importFileNameOutput = opts.importFileNameOutput || null;
    const reloadPage = typeof opts.reloadPage === "function"
      ? opts.reloadPage
      : (() => {
          window.location.reload();
        });

    function setImportFileName(fileName) {
      if (!importFileNameOutput) {
        return;
      }
      const normalized = String(fileName || "").trim();
      importFileNameOutput.textContent = normalized || tr("share_center_import_no_file_selected", "No file selected.");
    }

    async function readImportPayloadFromFile() {
      if (!importFileInput) {
        throw new Error(tr("share_center_error_choose_import_file", "Choose a share file first."));
      }
      const file = importFileInput.files && importFileInput.files[0];
      if (!file) {
        throw new Error(tr("share_center_error_choose_import_file", "Choose a share file first."));
      }
      setImportFileName(file.name || "");
      let content = "";
      try {
        content = await file.text();
      } catch (_readError) {
        throw new Error(tr("share_center_error_read_import_file", "Failed to read selected file."));
      }
      const normalized = String(content || "").replace(/^\uFEFF/, "").trim();
      if (!normalized) {
        throw new Error(tr("share_center_error_import_payload_empty", "Selected file is empty."));
      }
      return normalized;
    }

    async function generateShareCode() {
      if (!rulesShareController || typeof rulesShareController.generateSharePayloadWithOptions !== "function") {
        return;
      }
      try {
        let envelope = null;
        let exportScope = "bundle";
        let ignoredCount = 0;
        const currentProfileId = getCurrentProfileId();
        if (isFullMode()) {
          exportScope = "profile";
          envelope = await rulesShareController.generateSharePayloadWithOptions({
            scope: exportScope,
            profileId: currentProfileId
          });
        } else {
          const resolution = shareCenterSelection.resolveGenerateSelection({
            plan: shareCenterSelection.resolveSelectionPlan(getSelectedLeafEntries()),
            tr,
            normalizePath
          });
          if (resolution.ok !== true) {
            setExportStatus(
              resolution.message || tr("share_center_error_cannot_generate_selection", "Cannot generate with current selection."),
              colors.ERROR
            );
            return;
          }
          const supportedTargets = Array.isArray(resolution.supportedTargets)
            ? resolution.supportedTargets
            : [];
          if (!supportedTargets.length) {
            setExportStatus(tr("share_center_error_no_custom_nodes", "No exportable custom nodes selected."), colors.ERROR);
            return;
          }
          ignoredCount = resolution.ignoredCount;
          if (supportedTargets.length === 1) {
            const target = supportedTargets[0];
            if (target.kind === "ruleset_item") {
              exportScope = "ruleset";
              envelope = await rulesShareController.generateSharePayloadWithOptions({
                scope: exportScope,
                profileId: currentProfileId,
                helperManager,
                rulesetPath: target.rulesetPath,
                rulesetName: target.rulesetName || target.label
              });
            } else if (target.kind === "module_item") {
              exportScope = "module_item";
              envelope = await rulesShareController.generateSharePayloadWithOptions({
                scope: exportScope,
                profileId: currentProfileId,
                moduleId: target.moduleId,
                targetLanguage: target.moduleTargetLanguage
              });
            } else if (target.kind === "srs_pair_item") {
              exportScope = "srs_pair";
              envelope = await rulesShareController.generateSharePayloadWithOptions({
                scope: exportScope,
                profileId: currentProfileId,
                helperManager,
                srsPair: target.srsPair
              });
            } else if (target.kind === "appearance_theme") {
              exportScope = "appearance_theme";
              envelope = await rulesShareController.generateSharePayloadWithOptions({
                scope: exportScope,
                profileId: currentProfileId
              });
            } else {
              exportScope = String(target.scope || "").trim() || "bundle";
              envelope = await rulesShareController.generateSharePayloadWithOptions({
                scope: exportScope,
                profileId: currentProfileId
              });
            }
          } else {
            const bundleTargets = supportedTargets.map((target) => {
              if (target.kind === "ruleset_item") {
                return {
                  kind: "ruleset",
                  rulesetPath: target.rulesetPath,
                  rulesetName: target.rulesetName || target.label
                };
              }
              if (target.kind === "profile_settings") {
                return { kind: "profile_settings" };
              }
              if (target.kind === "srs_pair_item") {
                return {
                  kind: "srs_pair",
                  pair: target.srsPair
                };
              }
              if (target.kind === "appearance_theme") {
                return { kind: "appearance_theme" };
              }
              if (target.kind === "module_item") {
                return {
                  kind: "module_item",
                  moduleId: target.moduleId,
                  targetLanguage: target.moduleTargetLanguage
                };
              }
              return { kind: target.kind };
            });
            exportScope = "bundle";
            envelope = await rulesShareController.generateSharePayloadWithOptions({
              scope: exportScope,
              profileId: currentProfileId,
              helperManager,
              bundleTargets
            });
          }
        }
        if (!envelope || typeof envelope !== "object") {
          throw new Error(tr("share_center_error_export_failed", "Failed to export file."));
        }
        const content = `${JSON.stringify(envelope, null, 2)}\n`;
        const fileName = resolveExportFileName(exportScope, currentProfileId);
        const sizeBytes = downloadJsonFile(content, fileName);
        updateSummary();
        let message = tr(
          "share_center_status_exported_file",
          `Exported ${fileName} (${formatByteSize(sizeBytes)}).`,
          [fileName, formatByteSize(sizeBytes)]
        );
        if (ignoredCount > 0) {
          message = tr(
            "share_center_status_exported_file_ignored",
            `${message} Ignored ${ignoredCount} unsupported selection(s).`,
            [message, String(ignoredCount)]
          );
        }
        setExportStatus(message, colors.SUCCESS);
      } catch (err) {
        const message = err && err.message ? err.message : tr("share_center_error_export_failed", "Failed to export file.");
        setExportStatus(message, colors.ERROR);
      }
    }

    async function importShareCode() {
      if (!rulesShareController || typeof rulesShareController.importShareCodeWithOptions !== "function") {
        return;
      }
      try {
        const payload = await readImportPayloadFromFile();
        const currentProfileId = getCurrentProfileId();
        const result = await rulesShareController.importShareCodeWithOptions({
          code: payload,
          useCjk: false,
          profileId: currentProfileId,
          helperManager
        });
        if (result && result.scope === "ruleset") {
          await syncForProfile({ profileId: currentProfileId });
          const name = result.ruleset && result.ruleset.name ? result.ruleset.name : tr("share_center_group_rulesets", "ruleset");
          setImportStatus(
            tr(
              "share_center_status_ruleset_imported_enabled",
              `Imported ${name} and enabled it for this profile.`,
              [name]
            ),
            colors.SUCCESS
          );
          return;
        }
        if (result && result.scope === "module_item") {
          await syncForProfile({ profileId: currentProfileId });
          const moduleId = result.module && result.module.moduleId
            ? result.module.moduleId
            : tr("share_center_group_modules", "module");
          setImportStatus(
            tr(
              "share_center_status_module_imported",
              `Imported module preferences for ${moduleId}.`,
              [moduleId]
            ),
            colors.SUCCESS
          );
          return;
        }
        if (result && result.scope === "srs_pair") {
          setImportStatus(tr("share_center_status_srs_pair_imported_reload", "SRS pair progress imported. Reloading options…"), colors.SUCCESS);
          setTimeout(() => {
            reloadPage();
          }, 120);
          return;
        }
        if (result && result.scope === "appearance_theme") {
          setImportStatus(tr("share_center_status_appearance_imported_reload", "Appearance imported. Reloading options…"), colors.SUCCESS);
          setTimeout(() => {
            reloadPage();
          }, 120);
          return;
        }
        if (result && result.scope === "bundle") {
          const importedRulesets = Array.isArray(result.rulesets) ? result.rulesets : [];
          const importedModules = Array.isArray(result.modules) ? result.modules : [];
          const importedSrsPairs = Array.isArray(result.srsPairs) ? result.srsPairs : [];
          const importedRulesetsCount = importedRulesets.length;
          const importedModulesCount = importedModules.length;
          const importedSrsPairCount = importedSrsPairs.length > 0
            ? importedSrsPairs.length
            : (result.srsPair ? 1 : 0);
          const importedAppearance = Boolean(result.appearanceTheme);
          if (result.requiresReload === true || result.appliedProfileSettings === true) {
            const summaryParts = [];
            if (importedRulesetsCount > 0) {
              summaryParts.push(
                tr("share_center_summary_part_rulesets", `${importedRulesetsCount} rulesets`, [String(importedRulesetsCount)])
              );
            }
            if (importedModulesCount > 0) {
              summaryParts.push(
                tr("share_center_summary_part_modules", `${importedModulesCount} module settings`, [String(importedModulesCount)])
              );
            }
            if (result.appliedProfileSettings === true) {
              summaryParts.push(tr("share_center_summary_part_profile_settings", "profile settings"));
            }
            if (importedSrsPairCount > 0) {
              summaryParts.push(
                tr("share_center_summary_part_srs_pairs", `${importedSrsPairCount} SRS pairs`, [String(importedSrsPairCount)])
              );
            }
            if (importedAppearance) {
              summaryParts.push(tr("share_center_summary_part_appearance", "appearance"));
            }
            const summaryText = summaryParts.join(" / ");
            setImportStatus(
              summaryText
                ? tr(
                  "share_center_status_bundle_imported_reload_with_summary",
                  `Imported: ${summaryText}. Reloading options…`,
                  [summaryText]
                )
                : tr("share_center_status_bundle_imported_reload", "Bundle imported. Reloading options…"),
              colors.SUCCESS
            );
            setTimeout(() => {
              reloadPage();
            }, 120);
            return;
          }
          await syncForProfile({ profileId: currentProfileId });
          if (importedRulesetsCount > 0 && importedModulesCount > 0) {
            setImportStatus(
              tr(
                "share_center_status_bundle_imported_rulesets_modules",
                `Imported ${importedRulesetsCount} rulesets and ${importedModulesCount} module settings.`,
                [String(importedRulesetsCount), String(importedModulesCount)]
              ),
              colors.SUCCESS
            );
          } else if (importedRulesetsCount > 0) {
            setImportStatus(
              tr(
                "share_center_status_bundle_imported_rulesets",
                `Imported ${importedRulesetsCount} rulesets and enabled them for this profile.`,
                [String(importedRulesetsCount)]
              ),
              colors.SUCCESS
            );
          } else if (importedModulesCount > 0) {
            setImportStatus(
              tr(
                "share_center_status_bundle_imported_modules",
                `Imported ${importedModulesCount} module settings.`,
                [String(importedModulesCount)]
              ),
              colors.SUCCESS
            );
          } else {
            setImportStatus(tr("share_center_status_bundle_imported", "Bundle imported."), colors.SUCCESS);
          }
          return;
        }
        if (result && (result.scope === "srs" || result.scope === "profile")) {
          setImportStatus(tr("share_center_status_import_applied_reload", "Import applied. Reloading options…"), colors.SUCCESS);
          setTimeout(() => {
            reloadPage();
          }, 120);
          return;
        }
        setImportStatus(tr("share_center_status_payload_imported", "Payload imported."), colors.SUCCESS);
      } catch (err) {
        const message = err && err.message ? err.message : tr("share_center_error_invalid_payload", "Invalid payload.");
        setImportStatus(message, colors.ERROR);
      }
    }

    return {
      setImportFileName,
      readImportPayloadFromFile,
      generateShareCode,
      importShareCode
    };
  }

  root.optionsShareCenterWorkflows = {
    createWorkflows
  };
})();
