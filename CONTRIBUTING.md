# Contributing

I'm glad your reading this, hopefully that means you're about to contribute to this project in some way!

Please note though that while are contributions are welcome (as long as they follow the code of conduct below), not all
contributions can/will be accepted. If the change you are about to make is significant you should first discuss with the
repository owners in an issue, email or through similar means.

## Coding Style & Guidelines

### Code & markup

Because of the relatively small size of the project there are not a lot of specific guidelines currently enforced. That
said though, we do use [flake8](http://flake8.pycqa.org/) to check for some issues like long lines. It should
additionally be noted that there exist more [guidelines](https://www.python.org/dev/peps/pep-0008/) for Python code that
you might want to follow. For other languages (YAML, JavaScript, CSS, HTML, etc.) you should try to follow the style
used in the existing files.

### Commit messages

* If you're addressing a specific issue start the first line with `GH-###`
* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line (using GH-_###_ syntax)

## Before submitting a Pull Request

* Make sure that your code conforms to the _Coding Style & Guidelines_ section above.
* Update the `README.md` if required.
* Make sure that everything works by following the _Testing procedure_

## Testing procedure

This project does currently not include unit tests or similar, instead we here outline some manual testing steps that
should be performed before release, submitting/merging a PR, etc.

1. Run the generator
2. Run the validator
2. Open up the web interface
    1. Search for a couple different terms
    2. Open the pages for a couple packages, you should see each of the following at least once:
        * Code example
        * README
        * conanfile.py
        * Multiple authors
        * Multiple licenses
        * Multiple repos and versions (also try changing the version and repo)

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
  advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at jan@dalheimer.de. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

### Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at https://www.contributor-covenant.org/version/1/4/code-of-conduct.html

[homepage]: https://www.contributor-covenant.org
