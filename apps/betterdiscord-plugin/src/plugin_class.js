		return class LexiShift extends Plugin {
			onLoad () {
				this.defaults = {
					general: {
						targetMessages: {value: true, description: "Replace words in messages"}
					}
				};

				this.modulePatches = {
					before: ["Messages", "Message"],
					after: ["MessageContent"]
				};
			}

			onStart () {
				rules = BDFDB.DataUtils.load(this, "rules");
				if (!Array.isArray(rules)) rules = [];
				trie = buildTrie(normalizeRules(rules));
				oldMessages = {};
				this._loadPreferences();
				this._installStyle();
				this._startMarkerObserver();
				this.requestRefresh();
			}

			onStop () {
				this._removeStyle();
				this._stopMarkerObserver();
				this.requestRefresh();
			}

			getSettingsPanel () {
				return buildSettingsPanel(this);
			}

			requestRefresh () {
				if (typeof this.forceUpdateAll === "function") {
					this.forceUpdateAll();
					return;
				}
				if (BDFDB && BDFDB.PluginUtils && typeof BDFDB.PluginUtils.forceUpdateAll === "function") {
					BDFDB.PluginUtils.forceUpdateAll(this);
				}
			}

			processMessages (e) {
				if (!this.settings.general.targetMessages) return;
				e.instance.props.channelStream = [].concat(e.instance.props.channelStream);
				for (let i in e.instance.props.channelStream) {
					let message = e.instance.props.channelStream[i].content;
					if (message) {
						if (BDFDB.ArrayUtils.is(message.attachments)) this.checkMessage(e.instance.props.channelStream[i], message);
						else if (BDFDB.ArrayUtils.is(message)) for (let j in message) {
							let childMessage = message[j].content;
							if (childMessage && BDFDB.ArrayUtils.is(childMessage.attachments)) this.checkMessage(message[j], childMessage);
						}
					}
				}
			}

			processMessage (e) {
				if (!this.settings.general.targetMessages) return;
				let repliedMessage = e.instance.props.childrenRepliedMessage;
				if (repliedMessage && repliedMessage.props && repliedMessage.props.children && repliedMessage.props.children.props && repliedMessage.props.children.props.referencedMessage && repliedMessage.props.children.props.referencedMessage.message) {
					let message = repliedMessage.props.children.props.referencedMessage.message;
					if (oldMessages[message.id]) {
						let {content, embeds} = this.parseMessage(message);
						repliedMessage.props.children.props.referencedMessage.message = new BDFDB.DiscordObjects.Message(Object.assign({}, message, {content, embeds}));
					}
				}
			}

			processMessageContent (e) {
				if (!this.settings.general.targetMessages) return;
				if (!e || !e.returnvalue) return;
				const replaced = replaceMarkersInTree(e.returnvalue, this);
				if (Array.isArray(replaced)) {
					e.returnvalue = BdApi.React.createElement(BdApi.React.Fragment, null, ...replaced);
				}
				else {
					e.returnvalue = replaced;
				}
			}

			checkMessage (stream, message) {
				let {changed, content, embeds} = this.parseMessage(message);
				if (changed) {
					if (!oldMessages[message.id]) oldMessages[message.id] = new BDFDB.DiscordObjects.Message(message);
					stream.content.content = content;
					stream.content.embeds = embeds;
				}
				else if (oldMessages[message.id]) {
					stream.content.content = oldMessages[message.id].content;
					stream.content.embeds = oldMessages[message.id].embeds;
					delete oldMessages[message.id];
				}
			}

			parseMessage (message) {
				let content = message.content;
				let embeds = [].concat(message.embeds || []);
				let changed = false;
				if (content && typeof content == "string") {
					let replaced = replaceText(content, trie, {annotate: true});
					if (replaced !== content) {
						content = replaced;
						changed = true;
					}
				}
				if (embeds.length) {
					embeds = embeds.map(embed => {
						let raw = embed.rawDescription || embed.description;
						if (!raw || typeof raw !== "string") return embed;
						let replaced = replaceText(raw, trie, {annotate: false});
						if (replaced === raw) return embed;
						changed = true;
						return Object.assign({}, embed, {rawDescription: replaced, description: replaced});
					});
				}
				return {changed, content, embeds};
			}

			_loadPreferences () {
				const prefs = BDFDB.DataUtils.load(this, "prefs") || {};
				this._highlightReplacements = prefs.highlightReplacements !== false;
				this._highlightColor = prefs.highlightColor || "#9AA0A6";
			}

			_savePreferences () {
				BDFDB.DataUtils.save(
					{highlightReplacements: this._highlightReplacements, highlightColor: this._highlightColor},
					this,
					"prefs"
				);
			}

			getHighlightReplacements () {
				return this._highlightReplacements !== false;
			}

			setHighlightReplacements (value) {
				this._highlightReplacements = Boolean(value);
				this._savePreferences();
				this._applyHighlightToDom();
				this.requestRefresh();
			}

			getHighlightColor () {
				return this._highlightColor || "#9AA0A6";
			}

			setHighlightColor (value) {
				this._highlightColor = value || "#9AA0A6";
				this._savePreferences();
				this._applyHighlightToDom();
				this.requestRefresh();
			}

			_installStyle () {
				if (BdApi.DOM && typeof BdApi.DOM.addStyle === "function") {
					BdApi.DOM.addStyle(STYLE_ID, STYLE_RULES);
				}
			}

			_removeStyle () {
				if (BdApi.DOM && typeof BdApi.DOM.removeStyle === "function") {
					BdApi.DOM.removeStyle(STYLE_ID);
				}
			}

			_startMarkerObserver () {
				if (this._markerObserver || !document || !document.body) return;
				this._markerObserver = new MutationObserver(mutations => {
					if (this._markerReplacing) return;
					this._markerReplacing = true;
					try {
						for (const mutation of mutations) {
							for (const node of mutation.addedNodes) {
								if (node && node.nodeType === Node.ELEMENT_NODE) {
									replaceMarkersInElement(node, this);
								}
								else if (node && node.nodeType === Node.TEXT_NODE && node.nodeValue) {
									if (node.nodeValue.indexOf(MARKER_START) !== -1 && node.parentNode) {
										replaceMarkersInElement(node.parentNode, this);
									}
								}
							}
						}
					}
					finally {
						this._markerReplacing = false;
					}
				});
				this._markerObserver.observe(document.body, {childList: true, subtree: true});
				replaceMarkersInElement(document.body, this);
			}

			_stopMarkerObserver () {
				if (!this._markerObserver) return;
				this._markerObserver.disconnect();
				this._markerObserver = null;
			}

			_applyHighlightToDom () {
				if (!document) return;
				const highlight = this.getHighlightReplacements();
				const color = this.getHighlightColor();
				for (const node of document.querySelectorAll(".ls-replaced")) {
					if (highlight) {
						node.classList.add("ls-highlight");
						node.style.color = color;
					}
					else {
						node.classList.remove("ls-highlight");
						node.style.color = "";
					}
				}
			}
		};
