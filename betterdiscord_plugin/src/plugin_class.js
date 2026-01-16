		return class VocabReplacer extends Plugin {
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
				this.requestRefresh();
			}

			onStop () {
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
				return;
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
					let replaced = replaceText(content, trie);
					if (replaced !== content) {
						content = replaced;
						changed = true;
					}
				}
				if (embeds.length) {
					embeds = embeds.map(embed => {
						let raw = embed.rawDescription || embed.description;
						if (!raw || typeof raw !== "string") return embed;
						let replaced = replaceText(raw, trie);
						if (replaced === raw) return embed;
						changed = true;
						return Object.assign({}, embed, {rawDescription: replaced, description: replaced});
					});
				}
				return {changed, content, embeds};
			}
		};
