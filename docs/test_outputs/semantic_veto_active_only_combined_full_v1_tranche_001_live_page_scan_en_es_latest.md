# en-es Semantic Veto Live Page Scan

- Status: `ok`
- Decision: `manual_review_packet_ready`
- Scan: `en_es_active_only_prod_feel_pages_v1`
- Fixture data root: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root`
- Pages scanned: `9` / `17`
- Page fetch errors: `0`
- Scan stopped reason: `max_total_matches`
- Review rows: `80`
- Decision counts: `{'abstain': 29, 'replace': 51}`
- Decision source counts: `{'policy': 80}`

## How To Review

- `replace` means the user would see the Spanish replacement.
- `abstain` means the user would keep the original English text.
- Treat this as product-feel review, not a promotion metric.

## Pages

| Page | Status | Rows | Error | URL |
| --- | --- | ---: | --- | --- |
| `wikipedia_dentist` | `ok` | 10 |  | https://en.wikipedia.org/wiki/Dentist |
| `wikipedia_bar_establishment` | `ok` | 10 |  | https://en.wikipedia.org/wiki/Bar_(establishment) |
| `wikipedia_bar_music` | `ok` | 10 |  | https://en.wikipedia.org/wiki/Bar_(music) |
| `wikipedia_offset_computing` | `ok` | 10 |  | https://en.wikipedia.org/wiki/Offset_(computer_science) |
| `wikipedia_carbon_offset` | `ok` | 10 |  | https://en.wikipedia.org/wiki/Carbon_offset |
| `wikipedia_bridle` | `ok` | 10 |  | https://en.wikipedia.org/wiki/Bridle |
| `wikipedia_self_control` | `ok` | 10 |  | https://en.wikipedia.org/wiki/Self-control |
| `wikipedia_december` | `ok` | 9 |  | https://en.wikipedia.org/wiki/December |
| `wikipedia_tomorrow` | `ok` | 1 |  | https://en.wikipedia.org/wiki/Tomorrow |

## Review Rows

| Page | Trigger -> Target | Decision | Source | Active | Shadow | Margin | Your read | Sentence |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `wikipedia_dentist` | `dentist` -> `dentista` | `replace` | `policy` | 0.0565 | 0.0000 | 0.0565 |  | A dentist, also known as a dental doctor, dental physician, dental surgeon, is a health care professional who specializes in dentistry, the branch of medicine focused on the teeth, gums, and mouth. |
| `wikipedia_dentist` | `health` -> `salud` | `replace` | `policy` | 0.0315 | 0.0000 | 0.0315 |  | A dentist, also known as a dental doctor, dental physician, dental surgeon, is a health care professional who specializes in dentistry, the branch of medicine focused on the teeth, gums, and mouth. |
| `wikipedia_dentist` | `health` -> `salud` | `abstain` | `policy` | 0.0074 | 0.0000 | 0.0074 |  | The dentist's supporting team aids in providing oral health services. |
| `wikipedia_dentist` | `more` -> `más` | `abstain` | `policy` | 0.0141 | 0.0000 | 0.0141 |  | The first group, the Guild of Barbers, was created to distinguish more educated and qualified dental surgeons from lay barbers. |
| `wikipedia_dentist` | `work` -> `trabajar` | `abstain` | `policy` | 0.0082 | 0.0000 | 0.0082 |  | Ambroise Paré, often known as the Father of Surgery, published his own work about the proper maintenance and treatment of teeth. |
| `wikipedia_dentist` | `time` -> `hora` | `abstain` | `policy` | 0.0052 | 0.0000 | 0.0052 |  | Over time, trained dentists immigrated from Europe to the Americas to practice dentistry, and by 1760, America had its own native born practicing dentists. |
| `wikipedia_dentist` | `time` -> `hora` | `abstain` | `policy` | 0.0081 | 0.0000 | 0.0081 |  | Newspapers were used at the time to advertise and promote dental services. |
| `wikipedia_dentist` | `national` -> `nacional` | `replace` | `policy` | 0.0165 | 0.0000 | 0.0165 |  | In the 1840s, the world's first dental school and national dental organization were established. |
| `wikipedia_dentist` | `american` -> `americano` | `replace` | `policy` | 0.0318 | 0.0000 | 0.0318 |  | The American Dental Association was established in 1859 after a meeting with 26 dentists. |
| `wikipedia_dentist` | `among` -> `entre` | `abstain` | `policy` | 0.0130 | 0.0000 | 0.0130 |  | New dental boards, such as the National Association of Dental Examiners, were created to establish standards and uniformity among dentists. |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `abstain` | `policy` | 0.0307 | 0.1040 | -0.0733 |  | A bar, also known as a saloon, a tavern or tippling house, or sometimes as a pub or club, is a retail business that serves alcoholic beverages, such as beer, wine, liquor, cocktails, and other beverages such as mineral water and soft drinks. |
| `wikipedia_bar_establishment` | `pub` -> `taberna` | `replace` | `policy` | 0.0888 | 0.0000 | 0.0888 |  | A bar, also known as a saloon, a tavern or tippling house, or sometimes as a pub or club, is a retail business that serves alcoholic beverages, such as beer, wine, liquor, cocktails, and other beverages such as mineral water and soft drinks. |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `replace` | `policy` | 0.0931 | 0.0811 | 0.0120 |  | The term "bar" refers both to the countertop where drinks are prepared and served and also by extension to the entirety of the establishment in which the bar is located. |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `replace` | `policy` | 0.0895 | 0.0481 | 0.0414 |  | The term derives from the metal or wooden bar (barrier) that is often located along the length of the "bar". |
| `wikipedia_bar_establishment` | `century` -> `siglo` | `replace` | `policy` | 0.1280 | 0.0000 | 0.1280 |  | During the 19th century, saloons were very important to the leisure time of the working class. |
| `wikipedia_bar_establishment` | `time` -> `hora` | `replace` | `policy` | 0.0218 | 0.0000 | 0.0218 |  | During the 19th century, saloons were very important to the leisure time of the working class. |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `abstain` | `policy` | 0.0576 | 0.1100 | -0.0524 |  | Today, even when an establishment uses a different name, such as "tavern" or "saloon" or, in the United Kingdom, a "pub", the area of the establishment where the bartender pours or mixes beverages is normally called "the bar". |
| `wikipedia_bar_establishment` | `even` -> `par` | `replace` | `policy` | 0.0294 | 0.0000 | 0.0294 |  | Today, even when an establishment uses a different name, such as "tavern" or "saloon" or, in the United Kingdom, a "pub", the area of the establishment where the bartender pours or mixes beverages is normally called "the bar". |
| `wikipedia_bar_establishment` | `pub` -> `taberna` | `replace` | `policy` | 0.0592 | 0.0000 | 0.0592 |  | Today, even when an establishment uses a different name, such as "tavern" or "saloon" or, in the United Kingdom, a "pub", the area of the establishment where the bartender pours or mixes beverages is normally called "the bar". |
| `wikipedia_bar_establishment` | `century` -> `siglo` | `replace` | `policy` | 0.0568 | 0.0000 | 0.0568 |  | The sale and/or consumption of alcoholic beverages was prohibited in the first half of the 20th century in several countries. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `abstain` | `policy` | 0.0491 | 0.1115 | -0.0624 |  | In musical notation, a bar (or measure) is a segment of music bounded by vertical lines, known as bar lines (or barlines), usually indicating one or more recurring beats. |
| `wikipedia_bar_music` | `more` -> `más` | `abstain` | `policy` | 0.0000 | 0.0000 | 0.0000 |  | In musical notation, a bar (or measure) is a segment of music bounded by vertical lines, known as bar lines (or barlines), usually indicating one or more recurring beats. |
| `wikipedia_bar_music` | `music` -> `música` | `abstain` | `policy` | 0.0000 | 0.0000 | 0.0000 |  | In musical notation, a bar (or measure) is a segment of music bounded by vertical lines, known as bar lines (or barlines), usually indicating one or more recurring beats. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `replace` | `policy` | 0.0490 | 0.0000 | 0.0490 |  | The length of the bar, measured by the number of note values it contains, is normally indicated by the time signature. |
| `wikipedia_bar_music` | `time` -> `hora` | `replace` | `policy` | 0.0248 | 0.0000 | 0.0248 |  | The length of the bar, measured by the number of note values it contains, is normally indicated by the time signature. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `replace` | `policy` | 0.0704 | 0.0402 | 0.0302 |  | Types of bar lines Regular bar lines consist of a thin vertical line extending from the top line to the bottom line of the staff, sometimes also extending between staves in the case of a grand staff or a family of instruments in an orchestral score. |
| `wikipedia_bar_music` | `between` -> `entre` | `replace` | `policy` | 0.0231 | 0.0000 | 0.0231 |  | Types of bar lines Regular bar lines consist of a thin vertical line extending from the top line to the bottom line of the staff, sometimes also extending between staves in the case of a grand staff or a family of instruments in an orchestral score. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `replace` | `policy` | 0.1140 | 0.0779 | 0.0361 |  | A double bar line (or double bar) consists of two single bar lines drawn close together, separating two sections within a piece, or a bar line followed by a thicker bar line, indicating the end of a piece or movement. |
| `wikipedia_bar_music` | `close` -> `estrecho` | `replace` | `policy` | 0.0363 | 0.0000 | 0.0363 |  | A double bar line (or double bar) consists of two single bar lines drawn close together, separating two sections within a piece, or a bar line followed by a thicker bar line, indicating the end of a piece or movement. |
| `wikipedia_bar_music` | `double` -> `doble` | `replace` | `policy` | 0.0519 | 0.0000 | 0.0519 |  | A double bar line (or double bar) consists of two single bar lines drawn close together, separating two sections within a piece, or a bar line followed by a thicker bar line, indicating the end of a piece or movement. |
| `wikipedia_offset_computing` | `beginning` -> `principio` | `replace` | `policy` | 0.0422 | 0.0000 | 0.0422 |  | In computer science, an offset within an array or other data structure object is an integer indicating the distance (displacement) between the beginning of the object and a given element or point, presumably within the same object. |
| `wikipedia_offset_computing` | `between` -> `entre` | `replace` | `policy` | 0.0350 | 0.0000 | 0.0350 |  | In computer science, an offset within an array or other data structure object is an integer indicating the distance (displacement) between the beginning of the object and a given element or point, presumably within the same object. |
| `wikipedia_offset_computing` | `offset` -> `distancia` | `replace` | `policy` | 0.0957 | 0.0248 | 0.0709 |  | In computer science, an offset within an array or other data structure object is an integer indicating the distance (displacement) between the beginning of the object and a given element or point, presumably within the same object. |
| `wikipedia_offset_computing` | `only` -> `sólo` | `replace` | `policy` | 0.0216 | 0.0000 | 0.0216 |  | The concept of a distance is valid only if all elements of the object are of the same size (typically given in bytes or words). |
| `wikipedia_offset_computing` | `offset` -> `distancia` | `replace` | `policy` | 0.0643 | 0.0247 | 0.0396 |  | For example, if A is an array of characters containing "abcdef", the fourth element containing the character 'd' has an offset of three from the start of A. |
| `wikipedia_offset_computing` | `start` -> `principio` | `replace` | `policy` | 0.0508 | 0.0000 | 0.0508 |  | For example, if A is an array of characters containing "abcdef", the fourth element containing the character 'd' has an offset of three from the start of A. |
| `wikipedia_offset_computing` | `offset` -> `distancia` | `replace` | `policy` | 0.0320 | 0.0181 | 0.0139 |  | In assembly language In computer engineering and low-level programming (such as assembly language), an offset usually denotes the number of address locations added to a base address in order to get to a specific absolute address. |
| `wikipedia_offset_computing` | `offset` -> `distancia` | `replace` | `policy` | 0.0365 | 0.0000 | 0.0365 |  | In this (original) meaning of offset, only the basic address unit, usually the 8-bit byte, is used to specify the offset's size. |
| `wikipedia_offset_computing` | `only` -> `sólo` | `abstain` | `policy` | 0.0092 | 0.0000 | 0.0092 |  | In this (original) meaning of offset, only the basic address unit, usually the 8-bit byte, is used to specify the offset's size. |
| `wikipedia_offset_computing` | `between` -> `entre` | `abstain` | `policy` | 0.0041 | 0.0000 | 0.0041 |  | In IBM System/360 instructions, a 12-bit offset embedded within certain instructions provided a range of between 0 and 4096 bytes. |
| `wikipedia_carbon_offset` | `offset` -> `distancia` | `abstain` | `policy` | 0.0200 | 0.0165 | 0.0035 |  | Carbon offsetting is the practice of using carbon credits to offset or counter an entity's greenhouse gas inventory emissions in line with reporting programs or institutional emissions targets/goals. |
| `wikipedia_carbon_offset` | `offset` -> `distancia` | `abstain` | `policy` | 0.0318 | 0.0220 | 0.0097 |  | Carbon credit trading mechanisms (i.e., crediting programs), enable project developers to implement projects that mitigate GHGs and receive carbon credits which can be sold to interested buyers who may use the credits to claim they have offset their inventory GHG emissions. |
| `wikipedia_carbon_offset` | `work` -> `trabajar` | `abstain` | `policy` | 0.0060 | 0.0000 | 0.0060 |  | But each crediting program has its own list of approved methodologies, for example unless explicitly stated, an ACR approved methodology could not be used by someone trying to work through Verra's Verified Carbon Standard. |
| `wikipedia_carbon_offset` | `double` -> `doble` | `replace` | `policy` | 0.0212 | 0.0000 | 0.0212 |  | These include claims of overestimated carbon sequestration, double-counting of credits, and the failure of projects to provide "additional" environmental benefits beyond what would have occurred in the absence of the project. |
| `wikipedia_carbon_offset` | `between` -> `entre` | `abstain` | `policy` | 0.0085 | 0.0000 | 0.0085 |  | Article 6 of the Paris Agreement includes three mechanisms for "voluntary cooperation" between countries toward climate goals, including carbon credit markets. |
| `wikipedia_carbon_offset` | `more` -> `más` | `replace` | `policy` | 0.0205 | 0.0000 | 0.0205 |  | CDM projects may transition to become PACM projects if they meet the eligibility requirements and the Article 6.4 Methodology Panel is reviewing CDM (and other submitted methodologies) to determine if they meet the more rigorous standards of the PACM standard documents to be adopted by PACM to guide project development. |
| `wikipedia_carbon_offset` | `even` -> `par` | `abstain` | `policy` | 0.0059 | 0.0000 | 0.0059 |  | Forward crediting is a process where credits are issued for projected avoided emissions or enhanced removals, which can be claimed by buyers even before the reduction activities have occurred. |
| `wikipedia_carbon_offset` | `offset` -> `distancia` | `abstain` | `policy` | 0.0592 | 0.0875 | -0.0283 |  | The vintage of a carbon credit is the year in which a carbon credit was issued by a crediting program, which usually corresponds to the year in which a third party auditor reviews the project — generates the carbon offset credit is known as the vintage. |
| `wikipedia_carbon_offset` | `offset` -> `distancia` | `replace` | `policy` | 0.0424 | 0.0142 | 0.0282 |  | History In 1977, major amendments to the US Clean Air Act created one of the first tradable emission offset mechanisms, allowing permitted facilities to increase emissions in exchange for paying another company to reduce its emissions of the same pollutant by a greater amount. |
| `wikipedia_carbon_offset` | `among` -> `entre` | `replace` | `policy` | 0.0389 | 0.0000 | 0.0389 |  | Economics The economics behind programs such as the Kyoto Protocol was that the marginal cost of reducing emissions would differ among countries. |
| `wikipedia_bridle` | `bridle` -> `reprimir` | `abstain` | `policy` | 0.0066 | 0.0609 | -0.0543 |  | A bridle is a piece of equipment used to direct a horse. |
| `wikipedia_bridle` | `control` -> `gobernar` | `replace` | `policy` | 0.0321 | 0.0000 | 0.0321 |  | It provides additional control and communication through rein pressure. |
| `wikipedia_bridle` | `bridle` -> `reprimir` | `abstain` | `policy` | 0.0154 | 0.0876 | -0.0722 |  | Headgear without a bit that uses a noseband to control a horse is called a hackamore, or, in some areas, a bitless bridle. |
| `wikipedia_bridle` | `control` -> `gobernar` | `abstain` | `policy` | 0.0444 | 0.0454 | -0.0010 |  | Headgear without a bit that uses a noseband to control a horse is called a hackamore, or, in some areas, a bitless bridle. |
| `wikipedia_bridle` | `control` -> `gobernar` | `replace` | `policy` | 0.0325 | 0.0057 | 0.0268 |  | There are many different designs with many different name variations, but all use a noseband that is designed to exert pressure on sensitive areas of the animal's face to provide direction and control. |
| `wikipedia_bridle` | `face` -> `rostro` | `abstain` | `policy` | 0.0071 | 0.0000 | 0.0071 |  | There are many different designs with many different name variations, but all use a noseband that is designed to exert pressure on sensitive areas of the animal's face to provide direction and control. |
| `wikipedia_bridle` | `between` -> `entre` | `replace` | `policy` | 0.0233 | 0.0000 | 0.0233 |  | The bridle was devised by Indo-European herders of the Pontic-Caspian steppes to control horses between 3000 BC and 2000 BC. |
| `wikipedia_bridle` | `bridle` -> `reprimir` | `abstain` | `policy` | 0.0094 | 0.0000 | 0.0094 |  | The bridle was devised by Indo-European herders of the Pontic-Caspian steppes to control horses between 3000 BC and 2000 BC. |
| `wikipedia_bridle` | `control` -> `gobernar` | `replace` | `policy` | 0.0309 | 0.0000 | 0.0309 |  | The bridle was devised by Indo-European herders of the Pontic-Caspian steppes to control horses between 3000 BC and 2000 BC. |
| `wikipedia_bridle` | `bridle` -> `reprimir` | `replace` | `policy` | 0.0193 | 0.0081 | 0.0112 |  | Parts The bridle consists of the following elements: Crownpiece: The crownpiece, headstall (US) or headpiece (UK) goes over the horse's head just behind the animal's ears, at the poll. |
| `wikipedia_self_control` | `control` -> `gobernar` | `replace` | `policy` | 0.0622 | 0.0452 | 0.0170 |  | Self-control is the ability to regulate one's emotions, thoughts, and behavior in the face of temptations and impulses. |
| `wikipedia_self_control` | `face` -> `rostro` | `replace` | `policy` | 0.0179 | 0.0000 | 0.0179 |  | Self-control is the ability to regulate one's emotions, thoughts, and behavior in the face of temptations and impulses. |
| `wikipedia_self_control` | `control` -> `gobernar` | `replace` | `policy` | 0.0507 | 0.0362 | 0.0146 |  | Self-control is closely related to the ability to delay gratification, which refers to resisting immediate rewards in favor of larger or later benefits. |
| `wikipedia_self_control` | `control` -> `gobernar` | `abstain` | `policy` | 0.0144 | 0.0184 | -0.0040 |  | It is an aspect of inhibitory control, one of the core human executive functions. |
| `wikipedia_self_control` | `control` -> `gobernar` | `replace` | `policy` | 0.0582 | 0.0483 | 0.0099 |  | Neuroscientific research has identified the prefrontal cortex as a critical brain region involved in self-control, decision making, and the regulation of impulses. |
| `wikipedia_self_control` | `making` -> `producción` | `replace` | `policy` | 0.0160 | 0.0000 | 0.0160 |  | Neuroscientific research has identified the prefrontal cortex as a critical brain region involved in self-control, decision making, and the regulation of impulses. |
| `wikipedia_self_control` | `region` -> `comarca` | `replace` | `policy` | 0.0205 | 0.0123 | 0.0081 |  | Neuroscientific research has identified the prefrontal cortex as a critical brain region involved in self-control, decision making, and the regulation of impulses. |
| `wikipedia_self_control` | `making` -> `producción` | `abstain` | `policy` | 0.0000 | 0.0000 | 0.0000 |  | As an executive function, self-control supports goal-directed behavior, planning, and decision making. |
| `wikipedia_self_control` | `time` -> `hora` | `replace` | `policy` | 0.0329 | 0.0000 | 0.0329 |  | However, in the long term, the use of self-control can strengthen and improve the ability to control oneself over time. |
| `wikipedia_self_control` | `health` -> `salud` | `abstain` | `policy` | 0.0071 | 0.0000 | 0.0071 |  | When asked to rate the perceived appeal of different snacks before making a decision, people valued health bars over chocolate bars. |
| `wikipedia_december` | `december` -> `diciembre` | `replace` | `policy` | 0.2202 | 0.0000 | 0.2202 |  | December is the 12th and final month of the year in the Julian and Gregorian calendars. |
| `wikipedia_december` | `december` -> `diciembre` | `replace` | `policy` | 0.0670 | 0.0000 | 0.0670 |  | The winter days following December were not included as part of any month. |
| `wikipedia_december` | `beginning` -> `principio` | `replace` | `policy` | 0.0644 | 0.0000 | 0.0644 |  | Later, the months of January and February were created out of the monthless period and added to the beginning of the calendar, but December retained its name. |
| `wikipedia_december` | `december` -> `diciembre` | `replace` | `policy` | 0.0708 | 0.0000 | 0.0708 |  | Later, the months of January and February were created out of the monthless period and added to the beginning of the calendar, but December retained its name. |
| `wikipedia_december` | `december` -> `diciembre` | `replace` | `policy` | 0.1846 | 0.0000 | 0.1846 |  | December is the first month of winter in the Northern Hemisphere and the first month of summer in the Southern Hemisphere. |
| `wikipedia_december` | `june` -> `junio` | `abstain` | `policy` | 0.0487 | 0.0000 | 0.0487 |  | December in the Northern Hemisphere is the seasonal equivalent to June in the Southern Hemisphere and vice versa. |
| `wikipedia_december` | `beginning` -> `principio` | `replace` | `policy` | 0.0797 | 0.0000 | 0.0797 |  | In the Northern hemisphere, the beginning of the astronomical winter is traditionally 21 December or the date of the solstice. |
| `wikipedia_december` | `start` -> `principio` | `replace` | `policy` | 0.0557 | 0.0000 | 0.0557 |  | This shower can also start in November), the Phoenicids (November 29 to December 9, with a peak occurring around 5/6 December), the Quadrantids (typically a January shower but can also start in December), the Sigma Hydrids (December 4–15), and the Ursids (December 17-to December 25/26, peaking around December 22). |
| `wikipedia_december` | `official` -> `oficial` | `abstain` | `policy` | 0.0000 | 0.0000 | 0.0000 |  | Observances This list does not necessarily imply either official status or general observance. |
| `wikipedia_tomorrow` | `tomorrow` -> `mañana` | `replace` | `policy` | 0.0219 | 0.0000 | 0.0219 |  | Morrow, a supervillain from DC Comics Tomorrow "Tomo", a fictional character in the webtoon Live with Yourself! |
