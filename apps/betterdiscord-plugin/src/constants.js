var CJK_BASE_START = 0x4E00;
var CJK_BASE = 16384;

const MARKER_START = "\uE000LS:";
const MARKER_MID = "\uE001";
const MARKER_END = "\uE002";
const STYLE_ID = "lexishift-replacements";
const STYLE_RULES = `
.ls-replaced {
	cursor: pointer;
}
.ls-replaced.ls-highlight {
	color: var(--text-muted);
	transition: color 120ms ease;
}
.ls-replaced .ls-original {
	display: none;
}
.ls-replaced.ls-show-original .ls-replacement {
	display: none;
}
.ls-replaced.ls-show-original .ls-original {
	display: inline;
	color: var(--text-normal);
}
`;
