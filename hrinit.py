#! /usr/bin/env python3

import sys
import requests
import requests_cache
import os
import subprocess
import json
import argparse
import platform
import re
import email.utils
import datetime
import time
import logging


class Colors:
    """ Terminal colors """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"
    # cancel SGR codes if we don't write to a terminal
    if not __import__("sys").stdout.isatty():
        for c in dir():
            if isinstance(c, str) and c[0:2] != "__":
                locals()[c] = ""


class HackerRankParser():

    def __init__(self, debug=False, rootdir=None):
        self.debug = debug

        if rootdir is None:
            self.rootdir = os.path.dirname(__file__)
        else:
            self.rootdir = rootdir

        self.model = None

        self.path = None
        self.contest = None
        self.key = None

    def feed(self, data, ignore_path=False):
        if self.debug:
            with open("model.json", "w") as f:
                f.write(data)
            print("DEBUG: write model.json")

        data = json.loads(data)

        if data['status'] is True:
            self.model = m = data['model']

            if m['track'] is None:
                if m["primary_contest"] is None:
                    # challenge is not categorized (not a contest, no track)
                    if ignore_path:
                        self.path = "master"
                        self.path_name = "master"
                    else:
                        print("Cannot determine path for challenge {}".format(m['name']))
                        exit()
                else:
                    self.path = os.path.join("contests", m["contest_slug"])
                    self.path_name = "{}".format(m["primary_contest"]["name"])
            else:
                self.path = os.path.join(m["track"]["track_slug"], m["track"]["slug"])
                self.path_name = "{} > {}".format(m["track"]["track_name"], m["track"]["name"])

            self.contest = m['contest_slug']
            self.key = m['slug']

            if 'id' in m:
                self.challenge_id = m['id']
            else:
                self.challenge_id = None

            if m['contest_slug'] == "master":
                self.url = "https://www.hackerrank.com/challenges/{}/problem".format(self.key)
                self.url2 = None

                if 'primary_contest' in m:
                    if m['primary_contest'] and 'slug' in m['primary_contest']:
                        self.url2 = "https://www.hackerrank.com/contests/{}/challenges/{}".format(m['primary_contest']['slug'], self.key)  # noqa

            else:
                self.url = "https://www.hackerrank.com/contests/{}/challenges/{}".format(self.contest, self.key)  # noqa
                self.url2 = None

    def info(self):
        print(Colors.LIGHT_BLUE + "key     :" + Colors.END, self.model['slug'])
        print(Colors.LIGHT_BLUE + "name    :" + Colors.END, self.model['name'])
        print(Colors.LIGHT_BLUE + "domain  :" + Colors.END, self.path_name)
        print(Colors.LIGHT_BLUE + "preview :" + Colors.END, self.model['preview'])
        print(Colors.LIGHT_BLUE + "lang    :" + Colors.END, ','.join(self.model['languages']))

    def gen_stub(self, lang, overwrite=False, hpp=False, editor=True, add_test=True):
        """ create a file based on the hackerrank template with a significant header """
        EXTENSIONS = {"cpp": "cpp",
                      "cpp14": "cpp",
                      "c": "c",
                      "python3": "py",
                      "python": "py",
                      "haskell": "hs",
                      "bash": "sh",
                      "java": "java",
                      "java8": "java",
                      "javascript": "js",
                      "perl": "pl",
                      "lua": "lua",
                      "text": "txt",
                      "oracle": "sql"}

        PREFERED = ['python3', 'cpp14', 'c', 'haskell',
                    'bash', 'oracle', 'text', 'java8',
                    'python', 'javascript']

        # auto choose the language
        if lang == "*":
            if 'languages' in self.model:
                languages = self.model['languages']
                if len(languages) == 1:
                    lang = languages[0]
                else:
                    for i in PREFERED:
                        if i in languages:
                            lang = i
                            break
                    else:
                        print("Cannot choose automatically a language:", ' '.join(languages))
                        return
            else:
                print('Model unknown: no languages[]')
                return

        extension = EXTENSIONS.get(lang, lang)

        os.makedirs(os.path.join(self.rootdir, self.path), exist_ok=True)

        filename = os.path.join(self.rootdir, self.path, self.key + "." + extension)
        if not overwrite and os.path.exists(filename):
            print("File exists:", filename)
            return

        cmake = os.path.join(self.rootdir, self.path, "CMakeLists.txt")

        def write_header(f, comment, add_skeliton=True):

            def line(text=None):
                if text is None:
                    f.write('\n')
                else:
                    f.write(comment + text + '\n')

            def skeliton(what):
                text = self.model.get(lang + "_" + what, "").strip()
                if text != "":
                    if what.find("_tail") != -1:
                        line()
                        line('(' + what + ') ' + '-' * 70)
                    f.write(text + '\n')
                    if what.find("_head") != -1:
                        line('(' + what + ') ' + '-' * 70)
                        line()
                    return True
                else:
                    return False

            line(self.path_name + " > " + self.model['name'])
            if 'preview' in self.model:
                line(self.model['preview'])

            line('')
            line('{}'.format(self.url))
            if self.url2:
                line('{}'.format(self.url2))
            if self.challenge_id:
                line('challenge id: {}'.format(self.challenge_id))
            line('')
            line()

            if add_skeliton:
                skeliton("skeliton_head") or skeliton("template_head")
                skeliton("template")
                skeliton("skeliton_tail") or skeliton("template_tail")

        # langages avec testeur
        if lang == "cpp" or lang == "cpp14" or lang == "c":

            if hpp:
                filename_hpp = os.path.splitext(filename)[0] + ".hpp"

                with open(filename, "wt") as f:
                    write_header(f, '// ', add_skeliton=False)
                    f.write('\n')
                    f.write('#include "{}"\n'.format(os.path.basename(filename_hpp)))
                with open(filename_hpp, "wt") as f:
                    write_header(f, '// ', add_skeliton=True)

            else:
                with open(filename, "wt") as f:
                    write_header(f, '// ')

            with open(cmake, "at") as f:
                if add_test:
                    f.write("add_hackerrank({} {}.{})\n".format(self.key, self.key, lang[:3]))
                else:
                    f.write("add_executable({} {}.{})\n".format(self.key, self.key, lang[:3]))

        elif lang == "python3" or lang == "python":
            with open(filename, "wt") as f:
                write_header(f, '# ')
            with open(cmake, "at") as f:
                if add_test:
                    f.write("add_hackerrank_py({}.py)\n".format(self.key))
                else:
                    pass

        elif lang == "haskell":
            with open(filename, "wt") as f:
                write_header(f, '-- ')
            with open(cmake, "at") as f:
                f.write("#add_hackerrank_hs({}.hs)\n".format(self.key))

        elif lang == "bash":
            with open(filename, "wt") as f:
                write_header(f, '# ')
            with open(cmake, "at") as f:
                f.write("add_hackerrank_shell({}.sh)\n".format(self.key))

        elif lang == "java" or lang == "java8":
            with open(filename, "wt") as f:
                write_header(f, '// ')
            with open(cmake, "at") as f:
                f.write("add_hackerrank_java({}.java)\n".format(self.key))

        elif lang == "javascript":
            with open(filename, "wt") as f:
                write_header(f, '// ')
            with open(cmake, "at") as f:
                f.write("add_hackerrank_js({}.js)\n".format(self.key))

        # langages sans testeur
        elif lang == "text" or lang == "perl":
            with open(filename, "wt") as f:
                write_header(f, '# ')

        elif lang == "oracle" or lang == "lua":
            with open(filename, "wt") as f:
                write_header(f, '-- ')

        else:
            print("Unknown language:", lang)
            return

        filename = os.path.relpath(filename)

        print("File created. Use « code {} » to edit it.".format(filename))

        with open(os.path.join(self.rootdir, "history.md"), "at") as f:
            f.write("{}|{}|{}|{}|[solution]({}) [web]({})\n".format(
                self.path, self.key, lang, time.strftime("%c %z"),
                os.path.join(self.path, self.key + "." + extension),
                self.url))

        if editor:
            if 'VSCODE_PID' in os.environ:
                if platform.system() == 'Windows':
                    subprocess.check_call(["code.cmd", filename])
                else:
                    subprocess.check_call(["code", filename])

    def download(self,
                 dest_dir="testcases",
                 url="download_testcases",
                 suffix="-testcases.zip",
                 content_type="application/zip",
                 overwrite=False):
        """ download test cases and problem statement """

        def my_parsedate(text):
            return datetime.datetime(*email.utils.parsedate(text)[:6])

        testcases_dir = os.path.join(self.rootdir, dest_dir, self.contest)
        os.makedirs(testcases_dir, exist_ok=True)

        testcase_file = os.path.join(testcases_dir, self.key + suffix)
        testcase_err = os.path.splitext(testcase_file)[0] + ".err"

        if overwrite or (not os.path.exists(testcase_file) and not os.path.exists(testcase_err)):  # noqa

            offline = os.path.join(os.path.dirname(__file__),
                                   "offline", dest_dir, self.contest,
                                   self.key + suffix)
            if not overwrite and os.path.exists(offline):
                print("link", os.path.relpath(offline), os.path.relpath(testcase_file))
                os.link(offline, testcase_file)
                pass
            else:
                url = "https://www.hackerrank.com/rest/contests/{}/challenges/{}/{}".format(self.contest, self.key, url)  # noqa

                # download resource (statement or testcases: no cache)
                with requests_cache.disabled():
                    r = requests.get(url, allow_redirects=True)
                if r.status_code == 200:
                    if r.headers['content-type'] == content_type:
                        with open(testcase_file, "wb") as f:
                            f.write(r.content)

                        if r.headers.get('last-modified'):
                            d = my_parsedate(r.headers['last-modified'])
                            ts = d.timestamp()
                            os.utime(testcase_file, (ts, ts))

                        print("Download {}: {} bytes".format(dest_dir, len(r.content)))
                else:
                    print("{}: download error {} {} {}".format(dest_dir, self.key, r.status_code, r.text))
                    if r.status_code == 404:
                        with open(testcase_err, "w"):
                            pass
                    testcase_file = None

        return testcase_file

    def downloads(self, overwrite=False, testcases=True, statement=False):

        testcases_file, statement_file = None, None

        if testcases:
            testcases_file = self.download(overwrite=overwrite)

        if statement:
            statement_file = self.download(dest_dir="statements",
                                           url="download_pdf?language=English",
                                           suffix=".pdf",
                                           content_type="application/pdf",
                                           overwrite=overwrite)

        return testcases_file, statement_file


def set_logging(verbose):
    """ set up a colorized logger """
    if sys.stdout.isatty():
        logging.addLevelName(logging.DEBUG, "\033[0;32m%s\033[0m" % logging.getLevelName(logging.DEBUG))
        logging.addLevelName(logging.INFO, "\033[1;33m%s\033[0m" % logging.getLevelName(logging.INFO))
        logging.addLevelName(logging.WARNING, "\033[1;35m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
        logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

    if verbose:
        logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG, datefmt='%H:%M:%S')
    else:
        logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.ERROR, datefmt='%H:%M:%S')


def set_cache(refresh=False):
    """ install the static Requests cache """
    if refresh:
        expire_after = datetime.timedelta(seconds=0)
    else:
        expire_after = datetime.timedelta(days=30)
    requests_cache.install_cache(
            cache_name=os.path.join(os.path.dirname(__file__), "cache"),
            allowable_methods=('GET', 'POST'), expire_after=expire_after)
    requests_cache.core.remove_expired_responses()


def main():

    # grabbed from Javascript function we_are_hiring() in the www.hackerrank.com pages
    lines = [
        Colors.GREEN,
        "===============================================================================",
        ",--.  ,--.              ,--.                 ,------.                 ,--.     ",
        "|  '--'  | ,--,--. ,---.|  |,-. ,---. ,--.--.|  .--. ' ,--,--.,--,--, |  |,-.  ",
        "|  .--.  |' ,-.  || .--'|     /| .-. :|  .--'|  '--'.'' ,-.  ||      \\|     /  ",
        "|  |  |  |\\ '-'  |\\ `--.|  \\  \\\\   --.|  |   |  |\\  \\ \\ '-'  ||  ||  ||  \\  \\  ",
        "`--'  `--' `--`--' `---'`--'`--'`----'`--'   `--' '--' `--`--'`--''--'`--'`--' ",
        "===============================================================================",
        Colors.END,
    ]
    for i in lines:
        print(i)

    parser = argparse.ArgumentParser(
        description='Intialize a ' + Colors.LIGHT_BLUE + 'HackerRank' + Colors.END + ' challenge.')
    parser.add_argument('url', help="Challenge URL")
    parser.add_argument('-v', '--verbose', help="Verbose mode", action='store_true')
    parser.add_argument('-d', '--debug', help="Debug mode", action='store_true')
    parser.add_argument('-f', '--force', help="Force overwrite", action='store_true')
    parser.add_argument('-X', dest="force_cpp", help="Force C++", action='store_true')
    parser.add_argument('-H', dest="force_hpp", help="Force C++ with include", action='store_true')
    parser.add_argument('-C', dest="force_c", help="Force C", action='store_true')
    parser.add_argument('-l', dest="lang", metavar="LANG", help="Language selection", default="*")
    parser.add_argument('-R', "--refresh", help="force refresh cache", action='store_true')
    parser.add_argument("--no-cache", help="disable Requests cache", action='store_true')

    args = parser.parse_args()

    set_logging(args.verbose)
    if not args.no_cache:
        set_cache(args.refresh)

    if args.force_cpp or args.force_hpp:
        args.lang = "cpp14"
    if args.force_c:
        args.lang = "c"

    alt_path = None
    alt_path_name = None
    alt_url = None

    data = ""
    if args.url.startswith('http'):

        # challenge linked from the interview preparation kit ?
        t = re.search(r"www\.hackerrank\.com/challenges/([a-z\-\d]+)/problem\?h_l=playlist&slugs%5B%5D=interview&slugs%5B%5D=([a-z\-\d]+)&slugs%5B%5D=([a-z\-\d]+)", args.url)  # noqa
        if t:
            contest = "master"
            challenge = t.group(1)
            alt_path = os.path.join(t.group(2), t.group(3))

            # retrieve the name of the interview section
            url = "https://www.hackerrank.com/rest/playlists/" + t.group(2)
            r = requests.get(url)
            if r.status_code == 200:
                data = json.loads(r.content)
                name1 = data['name']
                name2 = [i['name'] for i in data['playlists'] if i['slug'] == t.group(3)][0]
                alt_path_name = "{} > {}".format(name1, name2)
            else:
                alt_path_name = alt_path

            alt_url = "https://www.hackerrank.com/challenges/{}/problem?h_l=playlist&slugs%5B%5D%5B%5D=interview&slugs%5B%5D%5B%5D={}&slugs%5B%5D%5B%5D={}".format(t.group(1), t.group(2), t.group(3))  # noqa

        else:
            # practice challenge ?
            t = re.search(r"www\.hackerrank\.com/challenges/([^/]+)", args.url)
            if t:
                contest = "master"
                challenge = t.group(1)

            else:
                # contest challenge ?
                t = re.search(r"www\.hackerrank\.com/contests/([^/]+)/challenges/([\w\d\-]+)", args.url)  # noqa
                if t:
                    contest = t.group(1)
                    challenge = t.group(2)

        # REST api to get challenge model
        url = "https://www.hackerrank.com/rest/contests/{}/challenges/{}".format(contest, challenge)

        r = requests.get(url)
        if r.status_code == 200:
            data = r.text

    elif args.url.find(':') != -1:
        contest, _, challenge = args.url.partition(':')
        url = "https://www.hackerrank.com/rest/contests/{}/challenges/{}".format(contest, challenge)
        print('URL', contest, challenge, url)

        r = requests.get(url)
        if r.status_code == 200:
            data = r.text

    else:
        with open(args.url) as f:
            data = f.read()

    parser = HackerRankParser(args.debug)
    parser.feed(data, True)

    # trick to manage "interview-preparation-kit" only challenge
    if alt_path:
        parser.path = alt_path
        parser.path_name = alt_path_name
        parser.url = alt_url

    parser.info()
    parser.gen_stub(args.lang, args.force, args.force_hpp)
    parser.downloads(args.force)


if __name__ == '__main__':
    main()
