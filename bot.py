from datetime import datetime
import signal
import copy
import ssl
import os
import re

import requests
import zirc

from config import config
import utils


class Bot(zirc.Client):

    def __init__(self):
        self.connection = zirc.Socket(wrapper=ssl.wrap_socket)
        self.config = config
        self.connect(self.config)
        self.start()

    def get_config(self, channel, key=None, default=None):
        channel = channel.lower()
        config = copy.deepcopy(self.config['chancfg'].get('default', {}))
        config.update(self.config['chancfg'].get(channel, {}))
        if key:
            return config.get(key, default)
        else:
            return config

    def parse_issue(self, channel, issue):
        domain = self.get_config(channel, 'domain', 'github.com')
        user = self.get_config(channel, 'user')
        repo = self.get_config(channel, 'repo')
        if re.match(r'^https?://github\.com/\S+/\S+/(issues|pull)/\d+(#\S+)?$',
                    issue):
            return {
                'domain': 'github.com',
                'user': issue.split('/')[3],
                'repo': issue.split('/')[4],
                'issue': issue.split('/')[6].split('#')[0],
                'url': True
            }
        elif re.match(r'^\S+\.\S+/\S+/\S+#\d+$', issue):
            return {
                'domain': issue.split('/', 2)[0],
                'user': issue.split('/', 2)[1],
                'repo': issue.split('/', 2)[2].split('#', 1)[0],
                'issue': issue.split('#', 1)[1]
            }
        elif re.match(r'^\S+/\S+#\d+$', issue):
            return {
                'domain': domain,
                'user': issue.split('/', 1)[0],
                'repo': issue.split('/', 1)[1].split('#', 1)[0],
                'issue': issue.split('#', 1)[1]
            }
        elif re.match(r'^\S+#\d+$', issue):
            return {
                'domain': domain,
                'user': user,
                'repo': issue.split('#', 1)[0],
                'issue': issue.split('#', 1)[1]
            }
        elif re.match(r'^#\d+$', issue):
            return {
                'domain': domain,
                'user': user,
                'repo': repo,
                'issue': issue.lstrip('#')
            }
        else:
            return None

    def github(self, issue):
        if not (issue['user'] and issue['repo']):
            return
        data = requests.get('https://api.github.com/repos/{0}/{1}/issues/{2}'
                            .format(issue['user'], issue['repo'],
                                    issue['issue']),
                            auth=tuple(self.config['auth']['github']))
        data = data.json()
        if data.get('message'):  # Something went wrong :(
            return
        reponame = '/'.join(
            [self.nohl(i) for i in data['repository_url'].split('/')[-2:]])
        if data.get('pull_request'):
            issuetype = 'Pull Request'
            data = requests.get(
                'https://api.github.com/repos/{0}/{1}/pulls/{2}'.format(
                    issue['user'], issue['repo'], issue['issue']),
                auth=tuple(self.config['auth']['github']))
            data = data.json()
            if data['state'] == 'closed' and data.get('merged'):
                data['state'] = 'merged'
        else:
            issuetype = 'Issue'
        if data['state'] == 'open':
            status = '\x0309OPEN\x0f'
        elif data['state'] == 'merged':
            status = '\x0306MERGED\x0f'
        else:
            status = '\x0304CLOSED\x0f'
        date_format = '%Y-%m-%dT%H:%M:%SZ'
        created_at = datetime.strptime(data['created_at'], date_format)
        msg = []
        msg.append('[\x02{0}\x02]'.format(reponame))
        msg.append('(\x02{0}) {1} \x02#{2}\x02: {3} opened by \x02{4}\x02 '
                   '{5} ago'.format(status, issuetype, data['number'],
                                    repr(data['title']),
                                    self.nohl(data['user']['login']),
                                    utils.timesince(created_at)))
        if data['state'] == 'closed':
            closed_at = datetime.strptime(data['closed_at'], date_format)
            msg.append('and closed by \x02{0}\x02 {1} ago'.format(
                self.nohl((data['closed_by'] or {'login': 'ghost'})['login']),
                utils.timesince(closed_at)))
        elif data['state'] == 'merged':
            merged_at = datetime.strptime(data['merged_at'], date_format)
            msg.append('and merged by \x02{0}\x02 {1} ago'.format(
                self.nohl((data['merged_by'] or {'login': 'ghost'})['login']),
                utils.timesince(merged_at)))
        if not issue.get('url'):
            msg.append('- {0}'.format(self.gitio(data['html_url'])))
        return ' '.join(msg)

    def nohl(self, string):
        string = list(string)
        string.insert(int(len(string)/2), '\u200b')
        return ''.join(string)

    def gitio(self, url):
        response = requests.post('https://git.io/', data={'url': url})
        return response.headers.get('Location', url)

    def on_privmsg(self, event, irc):
        if event.target == self._config['nickname']:  # Ignore PMs
            return
        if len(event.arguments) == 0:  # Ignore empty messages
            return
        issues = []
        for part in event.arguments[0].split(' '):
            issue = self.parse_issue(event.target, part)
            if issue and issue not in issues:
                issues.append(issue)
        for issue in issues[:2]:
            if issue['domain'] == 'github.com':
                msg = self.github(issue)
                if msg:
                    irc.reply(event, msg)

    def on_error(self, event, irc):
        os.kill(os.getpid(), signal.SIGINT)


if __name__ == '__main__':
    Bot()
