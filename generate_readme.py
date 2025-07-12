import json, re

with open('README.template.md') as f:
    template = f.read()

apptemp = str(template)
replacements = json.load(open('readme_partials/appversion.json'))
for k, v in replacements.items():
    apptemp = re.sub(r'{{' + re.escape(k) + r'}}', v, apptemp)
open('app/static/readme.md', 'w').write(apptemp)

gittemp = str(template)
replacements = json.load(open('readme_partials/gitversion.json'))
for k, v in replacements.items():
    gittemp = re.sub(r'{{' + re.escape(k) + r'}}', v, gittemp)
open('README.md', 'w').write(gittemp)
