import zirc

config = zirc.IRCConfig(
    host='chat.freenode.net',
    port=6697,
    nickname='Issues',
    ident='IssueBot',
    realname='IssueBot - https://code.libertas.tech/bs/IssueBot',
    channels=[],
    caps=zirc.Caps(zirc.Sasl(
        username='',
        password=''
    )),
    chancfg={  # This will probably become a JSON file
        'default': {
            'domain': 'github.com'
        }
    },
    auth={
        'github': ['Your GitHub Username', 'Your Personal Access Token']
    }
)
