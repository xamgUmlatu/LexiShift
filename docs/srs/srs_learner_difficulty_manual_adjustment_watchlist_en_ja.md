# en-ja Learner Difficulty Manual Adjustment Watchlist

Status: manual correction ledger for post-model overrides and review rows
Recorded: 2026-06-27 JST

Purpose: keep known one-off learner-difficulty presentation problems separate
from model-shape work. These rows should not drive another general model rule
unless they recur as a broad, source-computable pattern.

The machine-readable source of truth for active/review/watch adjustments is
`docs/test_inputs/srs_learner_difficulty_manual_corrections_en_ja.json`.

## Active Correction Rows

| Surface | Reading | Active correction | Why not model-driven now |
| --- | --- | --- | --- |
| `いい` | `いい` | Directly promote the kana row as the beginner-facing form of "good". | The model ranked `良い/よい` first and under-ranked the kana row, but this is a cross-row display/reading preference rather than a broad model shape. |
| `ワイシャツ` | `わいしゃつ` | Apply a small floor so it remains beginner-band, but no longer ranks before core early verbs/nouns. | It is easy and source-backed; the problem is first-page ordering, not a broad gairaigo rule. |
| `つく` | `つく` | Exclude from standalone SRS admission. | The kana row is too semantically overloaded; clearer kanji rows such as `着く/つく` and `付く/つく` should carry teachable meanings. |
| `居る` | `いる` | Keep the score early, but prefer display `いる`. | The lexical item is core; the written form is the presentation problem. |
| `居る` | `おる` | Raise and route as a variant reading. | It has strong dictionary/source support, so a broad source-confidence rule will not catch it safely. |
| `居` | `きょ` | Raise and route as a compound/Sino-Japanese morpheme. | It is valid inside compounds such as `住居` and `同居`, but does not work as ordinary beginner standalone SRS vocabulary. |
| `入る` | `いる` | Raise and route as a variant/compound-like reading. | `入る/はいる` is the core beginner standalone verb; `入る/いる` is valid vocabulary but should not be ordinary first-page SRS. |
| `後` | `ご` | Raise and route as a compound/affix reading. | The model sees a legitimate common reading, not whether the row is pedagogically standalone. |
| `後` | `のち` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but more written/formal than beginner-core `後/あと`. |
| `今日` | `こんにち` | Raise and route as a formal/written reading. | `今日/きょう` is the beginner word; standalone `こんにち` should not behave like ordinary early SRS vocabulary. |
| `中` | `ちゅう` | Raise and route as a compound/suffix reading. | `中/なか` is the beginner standalone row; `中/ちゅう` is mostly useful in compounds or suffix-like contexts. |
| `行き` | `いき` | Raise and route as a derived/suffix form. | `行く/いく` is the core beginner verb; `行き/いき` is mostly useful as a stem, destination, or suffix-like row. |
| `取り` | `とり` | Raise and route as a derived/suffix form. | `取る/とる` is the core verb; `取り/とり` is mostly useful as a stem or compound-forming row. |
| `上` | `じょう` | Raise and route as a compound/suffix reading. | `上/うえ` is the beginner standalone row; `上/じょう` is mostly useful in compounds or suffix-like contexts. |
| `上` | `かみ` | Raise and route as a formal/spatial variant. | `上/うえ` is the beginner standalone row; `上/かみ` is a later formal/spatial variant. |
| `下` | `げ` | Raise and route as a compound/suffix reading. | `下/した` is the beginner standalone row; `下/げ` is mostly useful in compounds or suffix-like contexts. |
| `夜` | `よ` | Move later within ordinary vocabulary. | It is valid vocabulary, but much later and more literary than beginner-core `夜/よる`. |
| `塩` | `えん` | Raise and route as an on-yomi compound reading. | `塩/しお` is the beginner standalone row; `塩/えん` is mainly useful inside compounds. |
| `魚` | `うお` | Move later within ordinary vocabulary. | It is valid vocabulary, but later than the beginner standalone row `魚/さかな`. |
| `体` | `てい` | Raise and route as a rare/technical reading. | `体/からだ` is the core beginner row; `体/てい` is not ordinary early SRS vocabulary. |
| `暇` | `いとま` | Move much later within ordinary vocabulary. | It is valid literary/formal vocabulary, but much later than ordinary `暇/ひま`. |
| `明く` | `あく` | Raise and route as a rare written variant. | It competes with easier `あく` rows and should not be ordinary early SRS vocabulary. |
| `眼鏡` | `がんきょう` | Raise and route as a rare/on-yomi reading. | `眼鏡/めがね` is the ordinary row; `眼鏡/がんきょう` should not be ordinary early SRS vocabulary. |
| `丈夫` | `じょうふ` | Raise and route as a rare reading. | `丈夫/じょうぶ` is the ordinary row; `丈夫/じょうふ` should not be ordinary early SRS vocabulary. |
| `上手` | `うわて` | Move later within ordinary vocabulary. | It is valid vocabulary, but later than the beginner row `上手/じょうず`. |
| `下` | `しも` | Move later within ordinary vocabulary. | It is valid vocabulary, but later and more formal/literary than beginner-core `下/した`. |
| `入り口` | `いりくち` | Raise and route as a variant reading. | `入り口/いりぐち` is the ordinary row; `入り口/いりくち` should not be ordinary early SRS vocabulary. |
| `南` | `なん` | Raise and route as a compound reading. | `南/みなみ` is the beginner standalone row; `南/なん` is mostly useful in compounds. |
| `東` | `あずま` | Move much later within ordinary vocabulary. | It is valid literary/regional vocabulary, but much later than ordinary `東/ひがし`. |
| `君` | `くん` | Raise and route as a suffix/title reading. | `君/きみ` is the ordinary standalone row; `君/くん` should not be ordinary early standalone SRS vocabulary. |
| `米` | `べい` | Raise and route as a compound/country reading. | `米/こめ` is the ordinary standalone row; `米/べい` is mostly useful in compounds. |
| `間` | `かん` | Raise and route as a compound/interval reading. | `間/あいだ` is the ordinary standalone row; `間/かん` is mostly useful in compounds or interval expressions. |
| `道` | `どう` | Raise and route as compound-reading-only vocabulary. | The model sees a legitimate common reading, not whether the row is pedagogically standalone. |
| `前` | `ぜん` | Raise and route as a compound/affix reading. | The model sees a legitimate common reading, not whether the row is pedagogically standalone. |
| `村` | `そん` | Raise and route as a compound/administrative reading. | Same-surface reading risk is too nuanced for the current general rule without damaging ordinary rows. |
| `下` | `もと` | Raise and route as a variant reading. | The current source evidence cannot reliably separate this from more basic readings of `下`. |
| `余り` | `あまり` | Keep the score early, but prefer display `あまり`. | The word is common and easy, but adverbial learner-facing display is usually kana. |
| `明日` | `あす` | Raise to the reviewed target neighborhood. | This is direct source-backed evidence conflicting with product presentation priority. |
| `葉書` | `はがき` | Move later within ordinary vocabulary while keeping kanji display. | The kanji spelling is acceptable, but the row is somewhat harder than its current early placement. |
| `段々` | `だんだん` | Keep the score early, but prefer display `だんだん`. | The word is easy, but early learner-facing display should prefer kana. |
| `眼鏡` | `めがね` | Keep the score early, but prefer display `めがね`. | The word is useful and early; kana is the cleaner learner-facing display. |
| `何時` | `いつ` | Keep the score early, but prefer display `いつ`. | The word is common and easy; kana is the cleaner learner-facing display. |
| `様` | `よう` | Keep the score early, but prefer display `よう`. | This reading is common, but early learner-facing display should prefer kana. |
| `筈` | `はず` | Keep the score early, but prefer display `はず`. | The word is common grammar-like vocabulary; kana is the cleaner learner-facing display. |
| `殆ど` | `ほとんど` | Keep the score early, but prefer display `ほとんど`. | The word is common; kana is the cleaner learner-facing display. |
| `何の` | `どの` | Keep the score early, but prefer display `どの`. | The word is common and easy; kana is the cleaner learner-facing display. |
| `中々` | `なかなか` | Keep the score early, but prefer display `なかなか`. | The word is common; kana is the cleaner learner-facing display. |
| `暫く` | `しばらく` | Keep the score early, but prefer display `しばらく`. | The word is common; kana is the cleaner learner-facing display. |
| `塵` | `ごみ` | Keep the score early, but prefer display `ごみ`. | The word is useful; kana is the cleaner learner-facing display for this reading. |
| `偶に` | `たまに` | Keep the score early, but prefer display `たまに`. | The word is common; kana is the cleaner learner-facing display. |
| `今日は` | `こんにちは` | Keep the score early, but prefer display `こんにちは`. | The greeting is learner-facing as kana rather than full 今日 は analysis. |
| `凄い` | `すごい` | Keep the score early, but prefer display `すごい`. | The word is common and useful; kana is the cleaner learner-facing display. |
| `始め` | `はじめ` | Keep the score early, but prefer display `はじめ`. | The word is easy, but standalone beginner-facing display is cleaner in kana. |
| `色々` | `いろいろ` | Keep the score early, but prefer display `いろいろ`. | The word is common and easy, but early learner-facing display usually prefers kana. |
| `来たる` | `きたる` | Raise and route as a formal/written variant. | This is source-normalization leakage, but broad normalized-only punishment can harm true easy forms. |
| `何処` | `どこ` | Keep the score early, but prefer display `どこ`. | The lexical item is easy; the written form is the presentation problem. |
| `御飯` | `ごはん` | Keep the score early, but prefer display `ご飯`. | The word is easy and common; full `御飯` is too stiff for early learner-facing display. |
| `煩い` | `うるさい` | Keep the score early, but prefer display `うるさい`. | The word is useful and early; the kanji form is too heavy for early learner-facing display. |
| `伯父` | `おじ` | Keep the score early, but prefer display `おじ`. | The concept is useful, but the specific `伯父` written distinction should not be foregrounded for early learners. |
| `家` | `うち` | Keep the score early, but prefer display `うち`. | The word is common and appropriate here; only the learner-facing written form needs smoothing. |
| `成る` | `なる` | Keep the score early, but prefer display `なる`. | The lexical item is core; the written form is the presentation problem. |
| `所` | `ところ` | Keep the score early, but prefer display `ところ`. | The lexical item is easy; the written form is the presentation problem. |
| `持ち` | `もち` | Move later and route as a derived/suffix form. | `持つ/もつ` is the core beginner verb; `持ち/もち` should not be ordinary beginner standalone SRS vocabulary. |
| `良い` | `よい` | Move later so `いい/いい` is exposed first. | `良い/よい` is valid and easy, but less suitable as the first beginner-facing row than `いい/いい`. |
| `身体` | `しんたい` | Move later within the early vocabulary band. | `体/からだ` should carry the core beginner body-word role; `身体/しんたい` is valid but more formal/written. |
| `鞄` | `かばん` | Keep the score early, but prefer display `かばん`. | The word is useful and early; the kanji form is too heavy for early learner-facing display. |
| `他` | `た` | Move later and route as a compound/formal reading. | `他/ほか` is the normal early standalone item; `他/た` should not be ordinary beginner standalone SRS vocabulary. |
| `奇麗` | `きれい` | Keep the score early, but prefer display `きれい`. | The lexical item is easy; the written form is the presentation problem. |
| `真っ直ぐ` | `まっすぐ` | Keep the score early, but prefer display `まっすぐ`. | The word is easy; kana is the cleaner early learner-facing form. |
| `出掛ける` | `でかける` | Keep the score early, but prefer display `出かける`. | The word is useful and correctly early; the full-kanji spelling is heavier than the normal learner-facing form. |
| `姉` | `ねえ` | Route as a variant/address reading. | `姉/あね` is the ordinary standalone vocabulary row; `姉/ねえ` should not be ordinary standalone SRS vocabulary. |
| `長` | `おさ` | Move much later within ordinary vocabulary. | It is valid literary/older vocabulary, but far too early beside ordinary beginner words. |
| `昨夜` | `さくや` | Move later within ordinary vocabulary. | It is a valid written/formal reading, but later than the surrounding beginner time words and conversational `昨夜/ゆうべ`. |
| `弾く` | `はじく` | Move later within ordinary vocabulary. | It is valid, but less beginner-core than `弾く/ひく`. |
| `戸` | `と` | Move later within ordinary vocabulary. | It is valid, but tougher for learners than the surrounding beginner nouns and better treated as a later concrete/counter-like item. |
| `園` | `その` | Move later within ordinary vocabulary. | It is valid, but too early beside beginner nouns and ordinary garden/place vocabulary. |
| `字引き` | `じびき` | Move later within ordinary vocabulary. | It is an old-fashioned dictionary word; `辞書/じしょ` should carry the early learner-facing role. |
| `都` | `と` | Route as an administrative/on-reading row. | It is valid, but should not be topic-stretched as ordinary standalone beginner vocabulary. |
| `易しい` | `やさしい` | Keep the score early, but prefer display `やさしい`. | The word is easy; kana is the cleaner early learner-facing form. |
| `画` | `が` | Move later and route as a compound/on-reading row. | It is valid kanji material, but not ordinary beginner standalone vocabulary. |
| `黄色` | `おうしょく` | Route as a formal/on-reading variant. | `黄色/きいろ` is the ordinary early color word; `おうしょく` should not behave like normal beginner standalone vocabulary. |
| `園` | `えん` | Move later and route as a compound/on-reading row. | The reading is valid, but mostly compound-like compared with more standalone garden/place vocabulary. |
| `苑` | `えん` | Move much later and route as rare/formal vocabulary. | Its early placement appears to come from source normalization rather than true beginner usefulness. |
| `伍` | `ご` | Move much later and route as rare/specialized vocabulary. | It is valid, but should not appear with ordinary beginner number or kanji rows. |
| `木` | `もく` | Move later and route as a compound/on-reading row. | `木/き` is the ordinary standalone row; `もく` is mostly useful in compounds or on-reading contexts. |
| `水` | `すい` | Move later and route as a compound/on-reading row. | `水/みず` is the ordinary standalone row; `すい` is mostly useful in compounds or on-reading contexts. |
| `古` | `いにしえ` | Move later within ordinary vocabulary. | It is valid literary vocabulary, but far too early beside beginner-core words. |
| `音` | `おん` | Route as a compound/on-reading row. | `音/おと` is the ordinary standalone row; `おん` should not be topic-stretched as normal standalone vocabulary. |
| `有る` | `ある` | Keep the score early, but prefer display `ある`. | The lexical item is core; the kanji spelling is the presentation problem. |
| `事` | `こと` | Keep the score early, but prefer display `こと`. | The word is common and grammar-like; kana is cleaner for early learner-facing display. |
| `頂く` | `いただく` | Keep the score early, but prefer display `いただく`. | The word is common/useful, but kana is cleaner for early learner-facing display. |
| `温い` | `ぬるい` | Keep the score early, but prefer display `ぬるい`. | The word is acceptable here; kana is the cleaner learner-facing display. |
| `尤も` | `もっとも` | Keep the score early, but prefer display `もっとも`. | The word is acceptable here; kana avoids foregrounding a heavier written form early. |
| `大分` | `だいぶ` | Keep the score early, but prefer display `だいぶ`. | The word is acceptable here; kana avoids foregrounding an awkward written form early. |
| `字` | `あざ` | Raise and route as a rare/place reading. | It is not ordinary standalone learner vocabulary and should not inherit the ease of common `字` rows. |
| `会` | `え` | Raise and route as a rare/bound reading. | The row is valid, but much less standalone-useful than common `会` readings and should not be topic-stretched as ordinary vocabulary. |
| `一言` | `いちげん` | Raise and route as a variant reading. | `一言/ひとこと` is the ordinary learner-facing row; this reading should not inherit that ease. |
| `現場` | `げんじょう` | Raise and route as a variant reading. | `現場/げんば` is the ordinary learner-facing row; this variant should not be ordinary early standalone SRS vocabulary. |
| `仏` | `ぶつ` | Raise and route as a compound/on-reading row. | `仏/ほとけ` is the more standalone learner row; `ぶつ` is mainly useful as an on-reading or compound-like row. |
| `土産` | `どさん` | Raise and route as a variant/compound reading. | `土産/みやげ` is the ordinary learner-facing word; this reading should not inherit that ease. |
| `夜中` | `やちゅう` | Raise and route as a rare/formal reading. | `夜中/よなか` is the ordinary learner-facing word; this reading is later/formal enough to restrict. |
| `鼠` | `ねず` | Raise and route as a bound/variant reading. | `鼠/ねずみ` is the ordinary standalone row; `ねず` is mostly bound/variant-like. |
| `根` | `こん` | Raise and route as a compound/on-reading row. | `根/ね` is the ordinary standalone row; `こん` is mainly useful as an on-reading or compound component. |
| `怒る` | `いかる` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but later and more written/literary than ordinary `怒る/おこる`. |
| `大事` | `おおごと` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but should not inherit the early learner priority of `大事/だいじ`. |
| `打つ` | `ぶつ` | Move later within ordinary vocabulary. | It is valid, but not as pedagogically central as ordinary `打つ/うつ`. |
| `音` | `ね` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but later and more literary/poetic than beginner-core `音/おと`. |
| `僕` | `しもべ` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but much later than the pronoun `僕/ぼく`. |
| `工場` | `こうば` | Move later within ordinary vocabulary. | It is useful enough to keep, but later than ordinary `工場/こうじょう` and too early in the current ranking. |
| `認める` | `したためる` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but much later and more literary/specific than `認める/みとめる`. |
| `国境` | `くにざかい` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but later than ordinary `国境/こっきょう` and too early through same-surface inheritance. |
| `女子` | `おなご` | Move later within ordinary vocabulary. | It is valid vocabulary, but archaic/regional compared with ordinary `女子/じょし`. |
| `敵` | `かたき` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but later and narrower than ordinary `敵/てき`. |
| `文` | `ふみ` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but literary/older compared with ordinary `文/ぶん`. |
| `奴` | `やっこ` | Move later within ordinary vocabulary. | It is valid vocabulary, but later and culturally/sense-specific compared with more common `奴` rows. |
| `辺` | `ほとり` | Move later within ordinary vocabulary. | It is valid descriptive vocabulary, but later/literary enough that its current placement is too early. |
| `質` | `しち` | Move later within ordinary vocabulary. | It is valid standalone vocabulary in specific senses, but later and narrower than ordinary `質/しつ`. |
| `癖` | `へき` | Move later within ordinary vocabulary. | It is a valid reading, but later/technical or compound-like compared with ordinary `癖/くせ`. |
| `包む` | `くるむ` | Move later within ordinary vocabulary. | It is valid and useful, but should not sit as early as easier same-surface or core wrapping verbs. |
| `床` | `とこ` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but later than ordinary `床/ゆか`. |
| `方々` | `ほうぼう` | Move later within ordinary vocabulary. | It is useful standalone vocabulary, but less central than `方々/かたがた` and too early through same-surface inheritance. |
| `柄` | `え` | Move later within ordinary vocabulary. | It is valid standalone vocabulary for a handle/grip/stem, but later than ordinary `柄/がら` and should not inherit its ease. |
| `流行` | `はやり` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but should sit later than the most beginner-friendly `流行` rows. |
| `金庫` | `かねぐら` | Move later within ordinary vocabulary. | It is valid vocabulary, but older/rarer than ordinary `金庫/きんこ`. |
| `汚れる` | `けがれる` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but later and more moral/literary than ordinary `汚れる/よごれる`. |
| `雷` | `いかずち` | Move later within ordinary vocabulary. | It is valid vocabulary, but more literary/marked than ordinary `雷/かみなり` and should be noticeably later. |
| `昼間` | `ちゅうかん` | Raise and route as a variant reading. | `昼間/ひるま` is the ordinary learner-facing row; this reading should not inherit that early placement or topic-stretch as ordinary standalone vocabulary. |
| `火` | `か` | Route as a compound/on-reading row. | `火/ひ` is the ordinary standalone learner row; `火/か` is mainly useful in compounds and calendar words such as `火事`, `火山`, and `火曜`. |
| `西` | `せい` | Route as a compound/directional reading. | `西/にし` is the ordinary standalone row; `西/せい` has tiny direct standalone support and is mainly useful in compounds such as `西洋`, `西暦`, and `西部`. |
| `東` | `とう` | Route as a compound/directional reading. | `東/ひがし` is the ordinary standalone row; `東/とう` is mainly useful in compounds such as `東洋`, `東西`, and `東北`. |
| `訳` | `やく` | Route as a compound/on-reading row. | `訳/わけ` is the clearer standalone learner row; `訳/やく` is misleading as standalone SRS and mainly appears through compounds such as `翻訳` and `通訳`. |
| `北` | `ほく` | Route as a compound/directional reading. | `北/きた` is the ordinary standalone row; `北/ほく` is mainly useful in compounds such as `北部`, `東北`, and `北東`. |
| `見` | `けん` | Route as a compound/on-reading row. | `見る/みる` carries the standalone learner-facing meaning; `見/けん` is mainly useful in compounds such as `発見`, `意見`, and `見物`. |
| `朝` | `ちょう` | Route as a compound/on-reading row. | `朝/あさ` is the ordinary standalone row; `朝/ちょう` is mainly useful in compounds such as `朝食`, `早朝`, `朝廷`, and `王朝`. |
| `地` | `じ` | Route as a compound/on-reading row. | It is common in compounds such as `地震`, `地面`, `地獄`, and `意地`, but not a clean ordinary standalone beginner SRS row. |
| `徒` | `と` | Route as a compound/on-reading row. | It is mainly useful in compounds such as `生徒`, `徒歩`, `信徒`, and `使徒` rather than ordinary standalone vocabulary. |
| `密` | `みつ` | Route as compound/bound material. | It is source-backed but mostly compound or bound-adjectival material in words such as `秘密`, `厳密`, `精密`, and `密度`. |
| `印` | `いん` | Route as a compound/on-reading row. | `印/しるし` is the clearer standalone learner row; `印/いん` is mostly useful in compounds such as `印象`, `印刷`, `消印`, and `封印`. |
| `半` | `はん` | Raise and route as compound/prefix-like material. | It is useful, but its very early score is inflated by compound/prefix-like usage such as `半分`, `半年`, `後半`, and `大半`. |
| `門` | `もん` | Move slightly later within ordinary vocabulary. | It is valid standalone vocabulary, but compound mass from `専門`, `部門`, and `入門` makes the current placement too early. |
| `角` | `かく` | Move slightly later within ordinary vocabulary. | It is valid vocabulary, but compound and technical/math uses inflate the row relative to cleaner beginner vocabulary. |
| `用` | `よう` | Raise and route as compound/function-heavy vocabulary. | It is highly compound/function-heavy in words such as `利用`, `使用`, `用意`, `作用`, and `信用`, so it should not behave like ordinary standalone beginner vocabulary. |
| `必用` | `ひつよう` | Raise and route as an uncommon spelling variant. | `必要/ひつよう` is the ordinary learner-facing word; `必用` is source-backed but should not appear as ordinary early standalone SRS vocabulary. |
| `市` | `いち` | Move later within ordinary vocabulary. | It is valid in market/fair senses, but narrower and later than ordinary `市/し` or city/civic vocabulary. |
| `山` | `さん` | Raise and route as compound/on-reading material. | `山/やま` is the ordinary standalone row; `山/さん` is mainly useful in compounds, names, or Sino-Japanese readings. |
| `高` | `こう` | Raise and route as compound/on-reading material. | `高い/たかい` carries the ordinary learner-facing adjective; `高/こう` is mainly useful in compounds or bound readings. |
| `けつまんこ` | `けつまんこ` | Route as sensitive/adult vocabulary. | The difficulty score is already tail-level, but it should not enter ordinary default standalone SRS admission. |
| `吐く` | `つく` | Raise and route as a variant reading. | JLPT lists this exact pair, but product presentation wants the ordinary `つく` meanings carried by clearer written forms. |
| `時々` | `じじ` | Raise and route as a rare reading. | `時々/ときどき` is the ordinary learner-facing row; `時々/じじ` should not inherit that beginner placement. |
| `何人` | `なにびと` | Raise and route as a rare/literary reading. | `何人/なんにん` carries the ordinary count/person-question role; `何人/なにびと` is rare/literary. |
| `家` | `や` | Raise and route as a rare/bound reading. | `家/いえ` and `家/うち` cover the ordinary learner-facing meanings; `家/や` has tiny exact standalone support. |
| `間` | `あい` | Raise and route as a rare/literary reading. | `間/あいだ` is the ordinary learner-facing row; `間/あい` should not inherit early lesson support from the surface. |
| `面` | `おも` | Raise and route as a marked/literary reading. | It is valid, but marked compared with ordinary face/surface vocabulary and should not be ordinary early standalone SRS. |
| `何時` | `なんどき` | Raise and route as a marked written reading. | `何時/いつ` is the ordinary early row; `何時/なんどき` should not sit with beginner time words. |
| `君` | `きんじ` | Raise and route as a rare reading. | `君/きみ` and `君/くん` are the learner-relevant rows; `君/きんじ` has tiny exact support. |
| `海` | `あま` | Raise and route as a rare reading. | `海/うみ` is the ordinary standalone row; `海/あま` should not inherit early support from common sea vocabulary. |
| `一時` | `いちどき` | Raise and route as a variant reading. | `一時/ひととき` and `一時/いっとき` are more plausible learner-facing readings; `一時/いちどき` is later/variant. |
| `去年` | `こぞ` | Raise and route as an old/literary reading. | `去年/きょねん` is the ordinary beginner row; `去年/こぞ` is old/literary. |
| `昨日` | `きそ` | Raise and route as a rare/literary reading. | `昨日/きのう` is the ordinary beginner row; `昨日/きそ` should not inherit that placement. |
| `海` | `かい` | Raise and route as compound/on-reading material. | `海/うみ` is the ordinary standalone row; `海/かい` is mainly useful in compounds, names, or on-reading contexts. |
| `悪口` | `あっこう` | Raise and route as a variant reading. | `悪口/わるぐち` is the ordinary learner-facing row; `悪口/あっこう` should not inherit that placement. |
| `梅雨` | `ばいう` | Raise and route as a variant/on-reading form. | `梅雨/つゆ` is the ordinary learner-facing row; `梅雨/ばいう` is a later variant/on-reading form. |
| `上` | `へ` | Raise and route as a rare/old reading. | `上/うえ` is the ordinary standalone row; `上/へ` should not inherit early support from common `上` rows. |
| `傘` | `からかさ` | Raise and route as marked/specific vocabulary. | `傘/かさ` is the ordinary learner-facing row; `傘/からかさ` is marked/specific. |
| `妹` | `いも` | Raise and route as a rare/literary reading. | `妹/いもうと` is the ordinary learner-facing row; `妹/いも` should not inherit beginner placement. |
| `人気` | `ひとけ` | Move later within ordinary vocabulary. | It is valid standalone vocabulary, but should not sit near `人気/にんき` from same-surface inheritance. |
| `氏` | `うじ` | Move later within ordinary vocabulary. | It is valid clan/lineage vocabulary, but narrower and later than the current same-surface-supported placement. |
| `山中` | `やまなか` | Move later within ordinary vocabulary. | It is source-backed, but too specific and low-direct-support for early learner placement. |
| `間` | `あわい` | Raise and route as literary/marked vocabulary. | `間/あいだ` is the ordinary learner-facing row; `間/あわい` should not inherit early lesson support from the surface. |
| `遠` | `おち` | Raise and route as a rare/literary reading. | It has tiny exact support and should not appear as early ordinary standalone SRS vocabulary. |
| `同じい` | `おなじい` | Raise and route as obsolete/nonstandard-looking vocabulary. | `同じ/おなじ` is the ordinary learner-facing form; `同じい/おなじい` should not inherit early adjective support. |
| `大き` | `おおき` | Raise and route as a bound/stem form. | `大きい/おおきい` and `大きな/おおきな` are the ordinary learner-facing forms. |
| `渓` | `けい` | Raise and route as compound/on-reading material. | It is mainly useful as kanji/on-reading or compound material rather than ordinary early standalone vocabulary. |
| `闔` | `こう` | Raise and route as obscure kanji material. | It has tiny exact support and should not be ordinary standalone learner vocabulary. |
| `旧る` | `ふる` | Raise and route as a rare written variant. | Ordinary `古い/ふるい` and `古びる/ふるびる` families should carry learner-facing roles. |
| `曲` | `くせ` | Raise and route as an orthographic variant. | `癖/くせ` is the ordinary spelling for the learner-facing word. |
| `共` | `むた` | Raise and route as archaic/literary vocabulary. | `共/とも` carries ordinary learner-facing roles. |
| `己` | `つちのと` | Raise and route as specialized calendar material. | It is sexagenary-cycle material, not ordinary standalone vocabulary. |
| `紫` | `し` | Raise and route as compound/on-reading material. | `紫/むらさき` is the ordinary learner-facing color row. |
| `鯨` | `いさな` | Raise and route as literary vocabulary. | `鯨/くじら` is the ordinary learner-facing row. |

## Review Candidates

| Surface | Reading | Current issue | Likely action | Why not model-driven now |
| --- | --- | --- | --- | --- |
| _none_ | _none_ | The previous review candidates have been promoted to active corrections. | Continue using the generated admission-veto candidate review pack for the next layer. | New rows should still be reviewed before activation because the mechanical flags include false positives such as useful ordinary readings. |

## Watch-Only Rows

| Surface | Reading | Current stance |
| --- | --- | --- |
| `或いは` | `あるいは` | Acceptable for now. It is kana-preferred and somewhat written/formal, but not obviously bad enough to override manually. |
| `猶` | `なお` | Addressed by the orthographic overlay candidate; keep in sample review, but not a manual exception unless final ranking still places it too early. |
| `骨` | `こつ` | Reviewed as a same-surface family candidate and intentionally left unchanged for now. It is mechanically suspicious beside `骨/ほね`, but the standalone "knack/tip" sense is useful enough that the current `0.25-0.30` band is not obviously harmful. |

## Review Policy

Use manual overrides only for rows that are:

- visibly harmful in early learner presentation;
- clearly one-off or source-defect-like;
- not safely fixable with a broad model rule;
- stable after the final ranking candidate is generated.

Future manual override passes should happen against the corrected full ranking.
Prioritize the first `100` rows, then suspicious rows through the early bands
where a single bad item would be user-visible.
