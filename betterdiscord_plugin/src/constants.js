const TOKEN_RE = /[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*|\s+|[^\w\s]+/g;
const WORD_RE = /^[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*$/;

var CJK_BASE_START = 0x4E00;
var CJK_BASE = 16384;
