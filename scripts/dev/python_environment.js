"use strict";

const path = require("node:path");
const { spawnSync } = require("node:child_process");

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const SUPPORTED_PYTHON = Object.freeze({ major: 3, minor: 10 });

function addCandidate(candidates, seen, command, prefixArgs, source) {
	if (!command) {
		return;
	}
	const key = JSON.stringify([command, prefixArgs]);
	if (seen.has(key)) {
		return;
	}
	seen.add(key);
	candidates.push({ command, prefixArgs, source });
}

function venvCandidates(venvRoot, source) {
	return [
		{
			command: path.resolve(venvRoot, "Scripts", "python.exe"),
			prefixArgs: [],
			source,
		},
		{
			command: path.resolve(venvRoot, "bin", "python"),
			prefixArgs: [],
			source,
		},
	];
}

function resolveCandidates({
	repoRoot = REPO_ROOT,
	includeRepoVenv = true,
	includeEnvironment = true,
	includeSystem = true,
} = {}) {
	const candidates = [];
	const seen = new Set();
	if (includeRepoVenv) {
		for (const candidate of venvCandidates(path.resolve(repoRoot, ".venv"), "repo .venv")) {
			addCandidate(
				candidates,
				seen,
				candidate.command,
				candidate.prefixArgs,
				candidate.source
			);
		}
	}
	if (includeEnvironment) {
		for (const [name, value] of [
			["LEXISHIFT_PYTHON", process.env.LEXISHIFT_PYTHON],
			["PYTHON", process.env.PYTHON],
			["PYTHON3", process.env.PYTHON3],
		]) {
			addCandidate(candidates, seen, value, [], name);
		}
		if (process.env.VIRTUAL_ENV) {
			for (const candidate of venvCandidates(process.env.VIRTUAL_ENV, "active virtualenv")) {
				addCandidate(
					candidates,
					seen,
					candidate.command,
					candidate.prefixArgs,
					candidate.source
				);
			}
		}
	}
	if (includeSystem) {
		for (const candidate of [
			{ command: "python3.10", prefixArgs: [], source: "PATH" },
			{ command: "python3", prefixArgs: [], source: "PATH" },
			{ command: "python", prefixArgs: [], source: "PATH" },
			{ command: "py", prefixArgs: ["-3.10"], source: "Windows py launcher" },
		]) {
			addCandidate(
				candidates,
				seen,
				candidate.command,
				candidate.prefixArgs,
				candidate.source
			);
		}
	}
	return candidates;
}

function probePython(candidate) {
	const probeCode = [
		"import json, sys",
		"print(json.dumps({",
		"  'major': sys.version_info.major,",
		"  'minor': sys.version_info.minor,",
		"  'micro': sys.version_info.micro,",
		"  'executable': sys.executable,",
		"}))",
	].join("\n");
	const result = spawnSync(
		candidate.command,
		[...candidate.prefixArgs, "-c", probeCode],
		{ encoding: "utf8" }
	);
	if (result.error || result.status !== 0) {
		return null;
	}
	try {
		const payload = JSON.parse(String(result.stdout || "").trim());
		if (!Number.isInteger(payload.major) || !Number.isInteger(payload.minor)) {
			return null;
		}
		return payload;
	} catch (_error) {
		return null;
	}
}

function isSupportedVersion(version) {
	return Boolean(
		version
		&& version.major === SUPPORTED_PYTHON.major
		&& version.minor === SUPPORTED_PYTHON.minor
	);
}

function resolvePython(options = {}) {
	const rejected = [];
	for (const candidate of resolveCandidates(options)) {
		const version = probePython(candidate);
		if (!version) {
			continue;
		}
		if (!isSupportedVersion(version)) {
			rejected.push({ candidate, version });
			continue;
		}
		return { ...candidate, version, rejected };
	}
	return { candidate: null, rejected };
}

function formatVersion(version) {
	if (!version) {
		return "unknown";
	}
	return `${version.major}.${version.minor}.${version.micro}`;
}

module.exports = {
	REPO_ROOT,
	SUPPORTED_PYTHON,
	formatVersion,
	isSupportedVersion,
	probePython,
	resolveCandidates,
	resolvePython,
	venvCandidates,
};
