# en-ja SRS Topic Autotag Wikidata Exact-Label Lists

- Status: `ok`
- Decision: `wikidata_exact_label_list_has_topic_evidence`
- Generated: `2026-07-01T02:50:50+00:00`
- Eligible labels: `2912`
- Collections: `9`
- Evidence rows: `147 `
- SPARQL requests: `58`
- SPARQL cache hits: `0`

## Topics

| Topic | Rows | Lemmas | New vs current overlay |
| --- | ---: | ---: | ---: |
| `animals` | 5 | 5 | 3 |
| `anime_manga_pop_culture` | 1 | 1 | 0 |
| `computing_internet` | 24 | 23 | 19 |
| `food_cooking` | 69 | 66 | 33 |
| `games` | 1 | 1 | 1 |
| `music_media_entertainment` | 10 | 10 | 6 |
| `plants_nature` | 15 | 14 | 8 |
| `shopping_money` | 6 | 3 | 5 |
| `sports_fitness` | 16 | 16 | 5 |

## Collections

| Collection | Topic | Rows | Lemmas | New vs current overlay |
| --- | --- | ---: | ---: | ---: |
| `animals_birds` | `animals` | 5 | 5 | 3 |
| `anime_manga_comics` | `anime_manga_pop_culture` | 1 | 1 | 0 |
| `computing_software_web` | `computing_internet` | 24 | 23 | 19 |
| `food_dishes_drinks` | `food_cooking` | 69 | 66 | 33 |
| `games_named` | `games` | 1 | 1 | 1 |
| `music_instruments` | `music_media_entertainment` | 10 | 10 | 6 |
| `plants_flowers` | `plants_nature` | 15 | 14 | 8 |
| `shopping_currency` | `shopping_money` | 6 | 3 | 5 |
| `sports_named` | `sports_fitness` | 16 | 16 | 5 |

## Review Sample

| Topic | Lemma | Reading | Score | Collection | Wikidata item | Root | New? |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `animals` | `動物` | `どうぶつ` | 0.064153 | `animals_birds` | `Q729` animal | `Q729` animal | no |
| `animals` | `主婦` | `しゅふ` | 0.12089 | `animals_birds` | `Q38126150` housewife | `Q729` animal | yes |
| `animals` | `バス` | `ばす` | 0.117585 | `animals_birds` | `Q1224135` bass | `Q729` animal | yes |
| `animals` | `王` | `おう` | 0.207564 | `animals_birds` | `Q113672983` king regnant | `Q729` animal | yes |
| `anime_manga_pop_culture` | `漫画` | `まんが` | 0.123432 | `anime_manga_comics` | `Q1004` comics | `Q1004` comics | no |
| `computing_internet` | `新聞` | `しんぶん` | 0.046171 | `computing_software_web` | `Q11032` newspaper | `Q7397` software | yes |
| `computing_internet` | `雑誌` | `ざっし` | 0.07839 | `computing_software_web` | `Q41298` magazine | `Q7397` software | yes |
| `computing_internet` | `テレビ` | `てれび` | 0.1175 | `computing_software_web` | `Q289` television | `Q7397` software | yes |
| `computing_internet` | `設定` | `せってい` | 0.17709 | `computing_software_web` | `Q21043347` Settings | `Q7397` software | no |
| `computing_internet` | `メニュー` | `めにゅー` | 0.166808 | `computing_software_web` | `Q846925` menu | `Q7397` software | yes |
| `computing_internet` | `継続` | `けいぞく` | 0.23197 | `computing_software_web` | `Q1128903` continuation | `Q7397` software | yes |
| `computing_internet` | `コード` | `こーど` | 0.202818 | `computing_software_web` | `Q4994879` code | `Q40056` computer program | yes |
| `food_cooking` | `料理` | `りょうり` | 0.044369 | `food_dishes_drinks` | `Q746549` dish | `Q2095` food | no |
| `food_cooking` | `野菜` | `やさい` | 0.067203 | `food_dishes_drinks` | `Q11004` vegetable | `Q2095` food | no |
| `food_cooking` | `バター` | `ばたー` | 0.097542 | `food_dishes_drinks` | `Q34172` butter | `Q2095` food | no |
| `food_cooking` | `砂糖` | `さとう` | 0.100381 | `food_dishes_drinks` | `Q11002` sugar | `Q2095` food | no |
| `food_cooking` | `コーヒー` | `こーひー` | 0.117331 | `food_dishes_drinks` | `Q8486` coffee | `Q2095` food | no |
| `food_cooking` | `味噌` | `みそ` | 0.151554 | `food_dishes_drinks` | `Q235169` miso | `Q2095` food | no |
| `food_cooking` | `ジャム` | `じゃむ` | 0.160537 | `food_dishes_drinks` | `Q1269` jam | `Q746549` dish | no |
| `food_cooking` | `茶` | `ちゃ` | 0.207606 | `food_dishes_drinks` | `Q6097` tea | `Q2095` food | no |
| `food_cooking` | `スープ` | `すーぷ` | 0.205996 | `food_dishes_drinks` | `Q107289424` soup | `Q2095` food | no |
| `food_cooking` | `豆` | `まめ` | 0.250077 | `food_dishes_drinks` | `Q379813` bean | `Q2095` food | yes |
| `games` | `スカート` | `すかーと` | 0.100636 | `games_named` | `Q504577` Skat | `Q142714` card game | yes |
| `music_media_entertainment` | `ギター` | `ぎたー` | 0.101653 | `music_instruments` | `Q6607` guitar | `Q34379` musical instrument | no |
| `music_media_entertainment` | `ピアノ` | `ぴあの` | 0.16596 | `music_instruments` | `Q5994` piano | `Q34379` musical instrument | no |
| `music_media_entertainment` | `キーボード` | `きーぼーど` | 0.213157 | `music_instruments` | `Q1343007` electronic keyboard | `Q34379` musical instrument | yes |
| `plants_nature` | `花` | `はな` | 0.060085 | `plants_flowers` | `Q506` flower | `Q506` flower | no |
| `plants_nature` | `米` | `こめ` | 0.138771 | `plants_flowers` | `Q5090` rice | `Q756` plant | no |
| `plants_nature` | `タバコ` | `たばこ` | 0.17839 | `plants_flowers` | `Q181095` Nicotiana tabacum | `Q756` plant | yes |
| `plants_nature` | `植物` | `しょくぶつ` | 0.218242 | `plants_flowers` | `Q756` plant | `Q756` plant | no |
| `plants_nature` | `ハーブ` | `はーぶ` | 0.211631 | `plants_flowers` | `Q207123` herb | `Q756` plant | no |
| `plants_nature` | `豆` | `まめ` | 0.250077 | `plants_flowers` | `Q379813` bean | `Q756` plant | no |
| `shopping_money` | `文` | `ぶん` | 0.204682 | `shopping_currency` | `Q70019827` Ryukyuan mon | `Q8142` currency | yes |
| `shopping_money` | `ランド` | `らんど` | 0.232267 | `shopping_currency` | `Q181907` rand | `Q8142` currency | yes |
| `shopping_money` | `円` | `えん` | 0.25017 | `shopping_currency` | `Q8146` yen | `Q8142` currency | no |
| `sports_fitness` | `走る` | `はしる` | 0.053983 | `sports_named` | `Q105674` running | `Q349` sport | yes |
| `sports_fitness` | `スポーツ` | `すぽーつ` | 0.061441 | `sports_named` | `Q349` sport | `Q349` sport | no |
| `sports_fitness` | `登山` | `とざん` | 0.120042 | `sports_named` | `Q36908` mountaineering | `Q349` sport | no |
| `sports_fitness` | `スカート` | `すかーと` | 0.100636 | `sports_named` | `Q504577` Skat | `Q349` sport | yes |
| `sports_fitness` | `基本` | `きほん` | 0.172514 | `sports_named` | `Q11426409`  | `Q349` sport | yes |
| `sports_fitness` | `ゴルフ` | `ごるふ` | 0.17161 | `sports_named` | `Q5377` golf | `Q349` sport | no |
| `sports_fitness` | `回転` | `かいてん` | 0.214894 | `sports_named` | `Q4117409` slalom skiing | `Q349` sport | no |
| `sports_fitness` | `プロレス` | `ぷろれす` | 0.228199 | `sports_named` | `Q131359` professional wrestling | `Q349` sport | yes |
| `animals` | `卵` | `たまご` | 0.086695 | `animals_birds` | `Q935672` spawn | `Q729` animal | no |
| `computing_internet` | `ボタン` | `ぼたん` | 0.117839 | `computing_software_web` | `Q1335171` graphical button | `Q7397` software | yes |
| `computing_internet` | `設定` | `せってい` | 0.17709 | `computing_software_web` | `Q18357227` settings | `Q7397` software | no |
| `computing_internet` | `ブログ` | `ぶろぐ` | 0.170311 | `computing_software_web` | `Q30849` blog | `Q7397` software | no |
| `computing_internet` | `クライアント` | `くらいあんと` | 0.209852 | `computing_software_web` | `Q528166` client | `Q7397` software | yes |
| `food_cooking` | `牛肉` | `ぎゅうにく` | 0.079746 | `food_dishes_drinks` | `Q192628` beef | `Q2095` food | yes |
| `food_cooking` | `豚肉` | `ぶたにく` | 0.102161 | `food_dishes_drinks` | `Q191768` pork | `Q2095` food | yes |
| `food_cooking` | `パン` | `ぱん` | 0.117669 | `food_dishes_drinks` | `Q7802` bread | `Q2095` food | no |
| `food_cooking` | `鶏肉` | `けいにく` | 0.185105 | `food_dishes_drinks` | `Q864693` chicken as food | `Q2095` food | yes |
| `food_cooking` | `ステーキ` | `すてーき` | 0.161045 | `food_dishes_drinks` | `Q213062` steak | `Q2095` food | no |
| `food_cooking` | `脳` | `のう` | 0.212903 | `food_dishes_drinks` | `Q719458` brain as food | `Q2095` food | yes |
| `food_cooking` | `デザート` | `でざーと` | 0.206928 | `food_dishes_drinks` | `Q182940` dessert | `Q2095` food | yes |
| `food_cooking` | `強力` | `きょうりょく` | 0.250848 | `food_dishes_drinks` | `Q17219555` Gōriki | `Q2095` food | yes |
| `music_media_entertainment` | `バス` | `ばす` | 0.117585 | `music_instruments` | `Q27911` bass | `Q34379` musical instrument | no |
| `music_media_entertainment` | `コース` | `こーす` | 0.177938 | `music_instruments` | `Q2001047` course | `Q34379` musical instrument | yes |
| `music_media_entertainment` | `ロケット` | `ろけっと` | 0.213877 | `music_instruments` | `Q7355086` rocket | `Q34379` musical instrument | yes |
| `plants_nature` | `野菜` | `やさい` | 0.067203 | `plants_flowers` | `Q11004` vegetable | `Q756` plant | yes |
| `plants_nature` | `トマト` | `とまと` | 0.179859 | `plants_flowers` | `Q20638126` tomato | `Q756` plant | yes |
| `plants_nature` | `レタス` | `れたす` | 0.231292 | `plants_flowers` | `Q83193` Lactuca sativa | `Q756` plant | yes |
| `plants_nature` | `松` | `まつ` | 0.250909 | `plants_flowers` | `Q59668787` pine tree | `Q756` plant | no |
| `shopping_money` | `文` | `ぶん` | 0.204682 | `shopping_currency` | `Q2751502` Japanese mon | `Q8142` currency | yes |
| `sports_fitness` | `散歩` | `さんぽ` | 0.09178 | `sports_named` | `Q1051130` strolling | `Q349` sport | yes |
| `sports_fitness` | `柔道` | `じゅうどう` | 0.136907 | `sports_named` | `Q11420` judo | `Q349` sport | no |
| `sports_fitness` | `テニス` | `てにす` | 0.120127 | `sports_named` | `Q847` tennis | `Q349` sport | no |
| `sports_fitness` | `スキー` | `すきー` | 0.171667 | `sports_named` | `Q130949` skiing | `Q349` sport | no |
| `sports_fitness` | `野球` | `やきゅう` | 0.240826 | `sports_named` | `Q5369` baseball | `Q349` sport | no |
| `computing_internet` | `ポスト` | `ぽすと` | 0.118941 | `computing_software_web` | `Q56119332` tweet | `Q7397` software | yes |
| `computing_internet` | `リスト` | `りすと` | 0.177542 | `computing_software_web` | `Q27948` list | `Q7397` software | yes |
| `computing_internet` | `シナリオ` | `しなりお` | 0.210826 | `computing_software_web` | `Q1000492` adventure | `Q40056` computer program | yes |
| `food_cooking` | `卵` | `たまご` | 0.086695 | `food_dishes_drinks` | `Q93189` egg as food | `Q2095` food | no |
| `food_cooking` | `果物` | `くだもの` | 0.105551 | `food_dishes_drinks` | `Q3314483` fruit | `Q2095` food | no |
| `food_cooking` | `カレー` | `かれー` | 0.118347 | `food_dishes_drinks` | `Q164606` curry | `Q2095` food | no |
| `food_cooking` | `酒` | `さけ` | 0.198729 | `food_dishes_drinks` | `Q154` alcoholic beverage | `Q40050` drink | no |
| `food_cooking` | `ケーキ` | `けーき` | 0.165904 | `food_dishes_drinks` | `Q13276` cake | `Q5159627` confection | no |
| `food_cooking` | `お好み焼き` | `おこのみやき` | 0.216507 | `food_dishes_drinks` | `Q701075` okonomiyaki | `Q2095` food | yes |
| `food_cooking` | `ウイスキー` | `ういすきー` | 0.210445 | `food_dishes_drinks` | `Q281` whisky | `Q40050` drink | yes |
| `music_media_entertainment` | `スプーン` | `すぷーん` | 0.119449 | `music_instruments` | `Q1879664` spoons | `Q34379` musical instrument | yes |
| `music_media_entertainment` | `ベース` | `べーす` | 0.183531 | `music_instruments` | `Q810447` bass | `Q34379` musical instrument | no |
| `music_media_entertainment` | `スピーカー` | `すぴーかー` | 0.214047 | `music_instruments` | `Q570` loudspeaker | `Q34379` musical instrument | yes |
| `plants_nature` | `木` | `き` | 0.069746 | `plants_flowers` | `Q10884` tree | `Q756` plant | no |
| `plants_nature` | `トマト` | `とまと` | 0.179859 | `plants_flowers` | `Q23501` tomato | `Q756` plant | yes |
| `plants_nature` | `メロン` | `めろん` | 0.234809 | `plants_flowers` | `Q81602` Cucumis melo | `Q756` plant | yes |
| `shopping_money` | `文` | `ぶん` | 0.204682 | `shopping_currency` | `Q6279611` cash | `Q8142` currency | yes |
| `sports_fitness` | `サイクリング` | `さいくりんぐ` | 0.120466 | `sports_named` | `Q53121` cycling | `Q349` sport | no |
| `sports_fitness` | `サッカー` | `さっかー` | 0.189463 | `sports_named` | `Q2736` association football | `Q349` sport | no |
| `computing_internet` | `フォーク` | `ふぉーく` | 0.11911 | `computing_software_web` | `Q332903` fork | `Q7397` software | yes |
| `computing_internet` | `プログラム` | `ぷろぐらむ` | 0.182232 | `computing_software_web` | `Q4303335` program | `Q7397` software | no |
| `computing_internet` | `ホスト` | `ほすと` | 0.216547 | `computing_software_web` | `Q829281` network host | `Q7397` software | no |
| `food_cooking` | `牛乳` | `ぎゅうにゅう` | 0.094153 | `food_dishes_drinks` | `Q10988133` cow's milk | `Q2095` food | no |
| `food_cooking` | `飴` | `あめ` | 0.106907 | `food_dishes_drinks` | `Q17238884` ame | `Q2095` food | yes |
| `food_cooking` | `サラダ` | `さらだ` | 0.166017 | `food_dishes_drinks` | `Q9266` salad | `Q2095` food | no |
| `food_cooking` | `食品` | `しょくひん` | 0.232775 | `food_dishes_drinks` | `Q951964` food product | `Q2095` food | no |
| `food_cooking` | `チーズ` | `ちーず` | 0.211123 | `food_dishes_drinks` | `Q10943` cheese | `Q2095` food | no |
| `music_media_entertainment` | `パイプ` | `ぱいぷ` | 0.198503 | `music_instruments` | `Q94994460` Pipe | `Q34379` musical instrument | yes |
| `plants_nature` | `オレンジ` | `おれんじ` | 0.184831 | `plants_flowers` | `Q3355098` Citrus sinensis | `Q756` plant | yes |
| `shopping_money` | `文` | `ぶん` | 0.204682 | `shopping_currency` | `Q3867091` Korean mun | `Q8142` currency | yes |
| `sports_fitness` | `ハイキング` | `はいきんぐ` | 0.120551 | `sports_named` | `Q12014035` hiking | `Q349` sport | no |

## Findings

- `PASS` `wikidata_list_evidence_generated`: Generated 147 exact-label list rows. Reading identity gate: accepted_kana_exact_surface=123, accepted_unique_surface_reading=82, rejected_ambiguous_surface_only=2.

## Limitations

- This is exact-label list evidence only; it is not a complete Wikidata topic inventory.
- Japanese aliases are disabled by default because aliases tend to reintroduce broad-sense noise.
- Rows generated here are mining evidence only; promotion should follow sample review and source-specific guards.
