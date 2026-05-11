# en-es Semantic Veto Live Page Scan

- Status: `ok`
- Decision: `manual_review_packet_ready`
- Scan: `en_es_active_only_prod_feel_pages_v1`
- Fixture data root: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-helper-runtime-smoke-data-root`
- Pages scanned: `17` / `17`
- Page fetch errors: `0`
- Scan stopped reason: `manifest_exhausted`
- Review rows: `63`
- Decision counts: `{'abstain': 50, 'replace': 13}`
- Decision source counts: `{'policy': 63}`

## How To Review

- `replace` means the user would see the Spanish replacement.
- `abstain` means the user would keep the original English text.
- Treat this as product-feel review, not a promotion metric.

## Pages

| Page | Status | Rows | Error | URL |
| --- | --- | ---: | --- | --- |
| `wikipedia_dentist` | `ok` | 8 |  | https://en.wikipedia.org/wiki/Dentist |
| `wikipedia_bar_establishment` | `ok` | 9 |  | https://en.wikipedia.org/wiki/Bar_(establishment) |
| `wikipedia_bar_music` | `ok` | 4 |  | https://en.wikipedia.org/wiki/Bar_(music) |
| `wikipedia_offset_computing` | `ok` | 0 |  | https://en.wikipedia.org/wiki/Offset_(computer_science) |
| `wikipedia_carbon_offset` | `ok` | 2 |  | https://en.wikipedia.org/wiki/Carbon_offset |
| `wikipedia_bridle` | `ok` | 7 |  | https://en.wikipedia.org/wiki/Bridle |
| `wikipedia_self_control` | `ok` | 7 |  | https://en.wikipedia.org/wiki/Self-control |
| `wikipedia_december` | `ok` | 0 |  | https://en.wikipedia.org/wiki/December |
| `wikipedia_tomorrow` | `ok` | 1 |  | https://en.wikipedia.org/wiki/Tomorrow |
| `wikipedia_heart` | `ok` | 7 |  | https://en.wikipedia.org/wiki/Heart |
| `wikipedia_brother` | `ok` | 0 |  | https://en.wikipedia.org/wiki/Brother |
| `wikipedia_rebate_marketing` | `ok` | 2 |  | https://en.wikipedia.org/wiki/Rebate_(marketing) |
| `wikipedia_smile` | `ok` | 5 |  | https://en.wikipedia.org/wiki/Smile |
| `wikipedia_governance` | `ok` | 8 |  | https://en.wikipedia.org/wiki/Governance |
| `wikipedia_bouillon_cube` | `ok` | 1 |  | https://en.wikipedia.org/wiki/Bouillon_cube |
| `wikipedia_chic` | `ok` | 1 |  | https://en.wikipedia.org/wiki/Chic |
| `wikipedia_salesperson` | `ok` | 1 |  | https://en.wikipedia.org/wiki/Salesperson |

## Review Rows

| Page | Trigger -> Target | Decision | Source | Active | Shadow | Margin | Your read | Sentence |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `wikipedia_dentist` | `dentist` -> `dentista` | `replace` | `policy` | 0.0571 | 0.0000 | 0.0571 |  | A dentist, also known as a dental doctor, dental physician, dental surgeon, is a health care professional who specializes in dentistry, the branch of medicine focused on the teeth, gums, and mouth. |
| `wikipedia_dentist` | `american` -> `americano` | `abstain` | `policy` | 0.0307 | 0.0000 | 0.0307 |  | The American Dental Association was established in 1859 after a meeting with 26 dentists. |
| `wikipedia_dentist` | `german` -> `alemán` | `abstain` | `policy` | 0.0122 | 0.0000 | 0.0122 |  | In 1895, the dental X-ray was discovered by a German physicist, Wilhelm Röntgen. |
| `wikipedia_dentist` | `dentist` -> `dentista` | `abstain` | `policy` | 0.0182 | 0.0000 | 0.0182 |  | Responsibilities By nature of their general training, a licensed dentist can carry out most dental treatments such as restorative (dental restorations, crowns, bridges), orthodontics (braces), prosthodontic (dentures, crown/bridge), endodontic (root canal) therapy, periodontal (gum) therapy, and oral surgery (extraction of teeth), as well as performing examinations, taking radiographs (x-rays) and diagnosis. |
| `wikipedia_dentist` | `american` -> `americano` | `replace` | `policy` | 0.0523 | 0.0000 | 0.0523 |  | United States In the US, dental specialties are recognized by the American Dental Association (ADA) or the American Board of Dental Specialties (ABDS) Currently, the ADA lists twelve dental specialties, who are recognized by the National Commission on Recognition of Dental Specialties and Certifying Boards, while the ABDS recognizes four dental specialty boards. |
| `wikipedia_dentist` | `control` -> `gobernar` | `abstain` | `policy` | 0.0198 | 0.0000 | 0.0198 |  | List of Dental Specialties under the ADA: Dental anesthesiology – The study and administration of general anesthesia, sedation, local anesthesia, and advanced methods of pain control. |
| `wikipedia_dentist` | `region` -> `comarca` | `abstain` | `policy` | 0.0228 | 0.0277 | -0.0049 |  | Oral medicine - the discipline of dentistry concerned with the oral health care of medically complex patients – including the diagnosis and management of medical conditions that affect the oral and maxillofacial region. |
| `wikipedia_dentist` | `region` -> `comarca` | `abstain` | `policy` | 0.0248 | 0.0142 | 0.0106 |  | Oral medicine – This specialty deals with the diagnosis and non-surgical management of patients with disorders related to the oral and maxillofacial region. |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `abstain` | `policy` | 0.0281 | 0.0968 | -0.0687 |  | A bar, also known as a saloon, a tavern or tippling house, or sometimes as a pub or club, is a retail business that serves alcoholic beverages, such as beer, wine, liquor, cocktails, and other beverages such as mineral water and soft drinks. |
| `wikipedia_bar_establishment` | `pub` -> `taberna` | `replace` | `policy` | 0.0865 | 0.0000 | 0.0865 |  | A bar, also known as a saloon, a tavern or tippling house, or sometimes as a pub or club, is a retail business that serves alcoholic beverages, such as beer, wine, liquor, cocktails, and other beverages such as mineral water and soft drinks. |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `replace` | `policy` | 0.0995 | 0.0830 | 0.0164 |  | The term "bar" refers both to the countertop where drinks are prepared and served and also by extension to the entirety of the establishment in which the bar is located. |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `replace` | `policy` | 0.0967 | 0.0468 | 0.0499 |  | The term derives from the metal or wooden bar (barrier) that is often located along the length of the "bar". |
| `wikipedia_bar_establishment` | `bar` -> `cercar` | `abstain` | `policy` | 0.0564 | 0.1102 | -0.0538 |  | Today, even when an establishment uses a different name, such as "tavern" or "saloon" or, in the United Kingdom, a "pub", the area of the establishment where the bartender pours or mixes beverages is normally called "the bar". |
| `wikipedia_bar_establishment` | `pub` -> `taberna` | `replace` | `policy` | 0.0605 | 0.0000 | 0.0605 |  | Today, even when an establishment uses a different name, such as "tavern" or "saloon" or, in the United Kingdom, a "pub", the area of the establishment where the bartender pours or mixes beverages is normally called "the bar". |
| `wikipedia_bar_establishment` | `pub` -> `taberna` | `abstain` | `policy` | 0.0344 | 0.0000 | 0.0344 |  | In many jurisdictions, if those under legal drinking age are allowed to enter, as is the case with pubs that serve food, they are not allowed to drink; in the U.S., there are 8 states where children may drink in a pub if accompanied by their parents. |
| `wikipedia_bar_establishment` | `pub` -> `taberna` | `abstain` | `policy` | 0.0340 | 0.0000 | 0.0340 |  | A brew pub has an on-site brewery and serves craft beers. |
| `wikipedia_bar_establishment` | `american` -> `americano` | `abstain` | `policy` | 0.0347 | 0.0000 | 0.0347 |  | "Fern bar" is an American slang term for an upscale or preppy (or yuppie) bar. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `abstain` | `policy` | 0.0498 | 0.1161 | -0.0662 |  | In musical notation, a bar (or measure) is a segment of music bounded by vertical lines, known as bar lines (or barlines), usually indicating one or more recurring beats. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `abstain` | `policy` | 0.0342 | 0.0000 | 0.0342 |  | The length of the bar, measured by the number of note values it contains, is normally indicated by the time signature. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `replace` | `policy` | 0.0699 | 0.0383 | 0.0316 |  | Types of bar lines Regular bar lines consist of a thin vertical line extending from the top line to the bottom line of the staff, sometimes also extending between staves in the case of a grand staff or a family of instruments in an orchestral score. |
| `wikipedia_bar_music` | `bar` -> `cercar` | `replace` | `policy` | 0.1058 | 0.0694 | 0.0364 |  | A double bar line (or double bar) consists of two single bar lines drawn close together, separating two sections within a piece, or a bar line followed by a thicker bar line, indicating the end of a piece or movement. |
| `wikipedia_carbon_offset` | `control` -> `gobernar` | `abstain` | `policy` | 0.0072 | 0.0116 | -0.0044 |  | Emissions trading systems Emissions trading are now an important element of regulatory programs to control pollution, including GHG emissions. |
| `wikipedia_carbon_offset` | `american` -> `americano` | `abstain` | `policy` | 0.0260 | 0.0000 | 0.0260 |  | They include the Verified Carbon Standard issued by Verra, the Gold Standard, the Global Carbon Council based in Qatar, the Climate Action Reserve, the American Carbon Registry, and Plan Vivo. |
| `wikipedia_bridle` | `control` -> `gobernar` | `abstain` | `policy` | 0.0290 | 0.0000 | 0.0290 |  | It provides additional control and communication through rein pressure. |
| `wikipedia_bridle` | `control` -> `gobernar` | `abstain` | `policy` | 0.0493 | 0.0403 | 0.0089 |  | Headgear without a bit that uses a noseband to control a horse is called a hackamore, or, in some areas, a bitless bridle. |
| `wikipedia_bridle` | `control` -> `gobernar` | `abstain` | `policy` | 0.0323 | 0.0049 | 0.0274 |  | There are many different designs with many different name variations, but all use a noseband that is designed to exert pressure on sensitive areas of the animal's face to provide direction and control. |
| `wikipedia_bridle` | `control` -> `gobernar` | `abstain` | `policy` | 0.0261 | 0.0000 | 0.0261 |  | The bridle was devised by Indo-European herders of the Pontic-Caspian steppes to control horses between 3000 BC and 2000 BC. |
| `wikipedia_bridle` | `american` -> `americano` | `replace` | `policy` | 0.0571 | 0.0000 | 0.0571 |  | Frentera, a strap running from the browband to the noseband, primarily seen on bridles of certain South American designs. |
| `wikipedia_bridle` | `bar` -> `cercar` | `replace` | `policy` | 0.0541 | 0.0221 | 0.0320 |  | Shank hobble: A strap, bar or chain that connects the shanks of a curb bit at the bottom of the bit. |
| `wikipedia_bridle` | `american` -> `americano` | `abstain` | `policy` | 0.0105 | 0.0000 | 0.0105 |  | Stock horse and working styles Western bridle: used for American-style western riding, this bridle usually does not have a noseband. |
| `wikipedia_self_control` | `control` -> `gobernar` | `replace` | `policy` | 0.0625 | 0.0521 | 0.0104 |  | Self-control is the ability to regulate one's emotions, thoughts, and behavior in the face of temptations and impulses. |
| `wikipedia_self_control` | `control` -> `gobernar` | `replace` | `policy` | 0.0576 | 0.0440 | 0.0137 |  | Self-control is closely related to the ability to delay gratification, which refers to resisting immediate rewards in favor of larger or later benefits. |
| `wikipedia_self_control` | `control` -> `gobernar` | `abstain` | `policy` | 0.0103 | 0.0170 | -0.0067 |  | It is an aspect of inhibitory control, one of the core human executive functions. |
| `wikipedia_self_control` | `control` -> `gobernar` | `abstain` | `policy` | 0.0541 | 0.0543 | -0.0002 |  | Neuroscientific research has identified the prefrontal cortex as a critical brain region involved in self-control, decision making, and the regulation of impulses. |
| `wikipedia_self_control` | `region` -> `comarca` | `abstain` | `policy` | 0.0218 | 0.0153 | 0.0065 |  | Neuroscientific research has identified the prefrontal cortex as a critical brain region involved in self-control, decision making, and the regulation of impulses. |
| `wikipedia_self_control` | `bar` -> `cercar` | `abstain` | `policy` | 0.0219 | 0.0208 | 0.0011 |  | They are also more likely to choose an apple over a candy bar in behavioral tasks. |
| `wikipedia_self_control` | `american` -> `americano` | `abstain` | `policy` | 0.0171 | 0.0000 | 0.0171 |  | The term draws on the American folk hero John Henry, whose legendary death followed intense physical labor; the concept has since been discussed in both academic and popular accounts of stress and health inequalities. |
| `wikipedia_tomorrow` | `tomorrow` -> `mañana` | `abstain` | `policy` | 0.0162 | 0.0000 | 0.0162 |  | Morrow, a supervillain from DC Comics Tomorrow "Tomo", a fictional character in the webtoon Live with Yourself! |
| `wikipedia_heart` | `control` -> `gobernar` | `abstain` | `policy` | 0.0230 | 0.0000 | 0.0230 |  | These nerves act to influence, but not control, the heart rate. |
| `wikipedia_heart` | `region` -> `comarca` | `abstain` | `policy` | 0.0283 | 0.0154 | 0.0129 |  | The heart derives from splanchnopleuric mesenchyme in the neural plate which forms the cardiogenic region. |
| `wikipedia_heart` | `control` -> `gobernar` | `replace` | `policy` | 0.0668 | 0.0082 | 0.0586 |  | The cardiovascular centres in the brainstem control the sympathetic and parasympathetic influences to the heart through the vagus nerve and sympathetic trunk. |
| `wikipedia_heart` | `control` -> `gobernar` | `abstain` | `policy` | 0.0099 | 0.0158 | -0.0059 |  | If medications fail to control an arrhythmia, another treatment option may be catheter ablation. |
| `wikipedia_heart` | `german` -> `alemán` | `abstain` | `policy` | 0.0000 | 0.0000 | 0.0000 |  | Otto Frank (1865–1944) was a German physiologist; among his many published works are detailed studies of this important heart relationship. |
| `wikipedia_heart` | `american` -> `americano` | `abstain` | `policy` | 0.0164 | 0.0000 | 0.0164 |  | The American surgeon Norman Shumway has been credited for his efforts to improve transplantation techniques, along with pioneers Richard Lower, Vladimir Demikhov and Adrian Kantrowitz. |
| `wikipedia_heart` | `russian` -> `ruso` | `abstain` | `policy` | 0.0271 | 0.0000 | 0.0271 |  | Many recipes combined them with other giblets, such as the Mexican pollo en menudencias and the Russian ragu iz kurinyikh potrokhov. |
| `wikipedia_rebate_marketing` | `american` -> `americano` | `abstain` | `policy` | 0.0140 | 0.0000 | 0.0140 |  | The typical American household that takes advantage of consumer rebates saves an average of $150 annually. |
| `wikipedia_rebate_marketing` | `american` -> `americano` | `abstain` | `policy` | 0.0095 | 0.0000 | 0.0095 |  | More than $8 billion was issued back to American households in 2011 alone by rebate programs. |
| `wikipedia_smile` | `smile` -> `sonreír` | `abstain` | `policy` | 0.1047 | 0.2305 | -0.1257 |  | A smile is a facial expression formed primarily by flexing the muscles at the sides of the mouth. |
| `wikipedia_smile` | `smile` -> `sonreír` | `abstain` | `policy` | 0.0470 | 0.0703 | -0.0233 |  | Some smiles include a contraction of the muscles at the corner of the eyes, an action known as a Duchenne smile. |
| `wikipedia_smile` | `smile` -> `sonreír` | `abstain` | `policy` | 0.0103 | 0.0192 | -0.0089 |  | Among humans, a smile expresses delight, sociability, happiness, joy, or amusement. |
| `wikipedia_smile` | `smile` -> `sonreír` | `abstain` | `policy` | 0.0065 | 0.0087 | -0.0022 |  | Evolutionary background Primatologist Signe Preuschoft traces the smile back over 30 million years of evolution to a "fear grin" stemming from monkeys and apes, who often used barely clenched teeth to portray to predators that they were harmless or to signal submission to more dominant group members. |
| `wikipedia_smile` | `american` -> `americano` | `abstain` | `policy` | 0.0210 | 0.0000 | 0.0210 |  | It is named after the now-defunct airline Pan American World Airways, whose flight attendants would always flash every passenger the same perfunctory smile. |
| `wikipedia_governance` | `govern` -> `gobernar` | `abstain` | `policy` | 0.0329 | 0.0133 | 0.0197 |  | A government may operate as a democracy where citizens vote on who should govern towards the goal of public good. |
| `wikipedia_governance` | `govern` -> `gobernar` | `abstain` | `policy` | 0.0382 | 0.0000 | 0.0382 |  | This considers the process by which governments are selected, monitored and replaced; the capacity of the government to effectively formulate and implement sound policies and the respect of citizens and the state of the institutions that govern economic and social interactions among them. |
| `wikipedia_governance` | `control` -> `gobernar` | `abstain` | `policy` | 0.0465 | 0.0187 | 0.0278 |  | An alternate definition sees governance as: the use of institutions, structures of authority and even collaboration to allocate resources and coordinate or control activity in society or the economy. |
| `wikipedia_governance` | `govern` -> `gobernar` | `abstain` | `policy` | 0.0184 | 0.0052 | 0.0132 |  | Absence of effective governance When a state fails to govern effectively, this does not simply imply the absence of the characteristics of effective governance. |
| `wikipedia_governance` | `control` -> `gobernar` | `abstain` | `policy` | 0.0134 | 0.0000 | 0.0134 |  | The project reports aggregate and individual indicators for more than 200 countries for six dimensions of governance: voice and accountability, political stability and lack of violence, government effectiveness, regulatory quality, rule of law, control of corruption. |
| `wikipedia_governance` | `region` -> `comarca` | `abstain` | `policy` | 0.0327 | 0.0263 | 0.0064 |  | For instance, in the European context, a health policy framework called Health 2020 Archived 2020-04-27 at the Wayback Machine was developed as a result of the collaboration between State members in the region. |
| `wikipedia_governance` | `control` -> `gobernar` | `abstain` | `policy` | 0.0371 | 0.0126 | 0.0245 |  | Corporate governance consists of the set of processes, customs, policies, laws and institutions affecting the way people direct, administer or control an organization. |
| `wikipedia_governance` | `control` -> `gobernar` | `abstain` | `policy` | 0.0358 | 0.0000 | 0.0358 |  | It consists of the policies, processes and institutions by which decisions about the access to, use of and control over land are made, implemented and enforced; it is also about managing and reconciling competing claims on land. |
| `wikipedia_bouillon_cube` | `german` -> `alemán` | `abstain` | `policy` | 0.0181 | 0.0000 | 0.0181 |  | Portable soup of less extended vintage was, according to the 1881 Household Cyclopedia, "exceedingly convenient for private families, for by putting one of the cakes in a saucepan with about a quart of water, and a little salt, a basin of good broth may be made in a few minutes." In the mid-19th century, German chemist Justus von Liebig developed meat extract, but it was more expensive than bouillon cubes. |
| `wikipedia_chic` | `german` -> `alemán` | `abstain` | `policy` | 0.0265 | 0.0000 | 0.0265 |  | There is a similar word in German, schick, with a meaning similar to chic, which may be the origin of the word in French; another theory links chic to the word chicane. |
| `wikipedia_salesperson` | `american` -> `americano` | `abstain` | `policy` | 0.0303 | 0.0000 | 0.0303 |  | Within these three tenets, the following definition of professional selling is offered by the American Society for Training and Development (ASTD): The holistic business system required to effectively develop, manage, enable, and execute a mutually beneficial, interpersonal exchange of goods or services for equitable value. |
