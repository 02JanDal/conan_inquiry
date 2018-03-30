# [Conan Inquiry](https://02jandal.github.io/conan_inquiry)

An alternative to the [official package search](conan.io/search) for conan packages. You can find it [here](https://02jandal.github.io/conan_inquiry).

## Features

* Search results updated-as-you-type
* Packages from repositories outside conan-central
* Quick information about what is packaged (description, licenses, authors, links, code example, etc.)
* View README, the `conanfile.py` and more

## Getting started

If you just want to report an error in an existing package or notify us about a missing package you can skip the steps
below and head straight to [reporting an issues](/issues/new).

This repository consist of three things:

* Static data files ([conan_inquiry/data/packages](https://github.com/02JanDal/conan_inquiry/tree/master/conan_inquiry/data/packages))
* Scripts to find new packages, generate the full JSON file from the static data files and validate the result ([conan_inquiry](https://github.com/02JanDal/conan_inquiry/tree/master/conan_inquiry))
* A web interface using the generated JSON ([conan_inquiry/data/web](https://github.com/02JanDal/conan_inquiry/tree/master/conan_inquiry/data/web))

### Workflow

When updating the list of packages the usual workflow is as follows:

1. At at least one package for each fully new repository
2. Run `conan_inquiry.py find` to find new packages
3. Run `conan_inquiry.py generate` (see below for more information) to gather additional data and generate an aggregated package file
4. Run `conan_inquiry.py validate` to find any missing fields (start from the top of the output)
    1. Fix _all_ (otherwise you'll waste ratelimit resource) issues it reports
    2. Repeat (generate -> validate -> fix) until there are no more issues
5. Copy `packages.js` to `conan_inquiry/data/web` and open `index.html` from the same file in a browser
6. Run `conan_inquiry.py deploy` to upload everything to a gh-pages branch

### Prerequisites

You need to have Git and Python 3 installed. Then clone the project using git and install the dependencies using pip:

```commandline
git clone https://github.com/02JanDal/conan_inquiry
cd conan_inquiry
pip install -r requirements.txt
```

**Note:** It is highly recommended that you use a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

### Using the generator

In order to be able to test/use the web interface you need to run the generator.

#### Getting your access tokens

In order to be able to run the generator you need a couple of access tokens to different sites.

* Github client ID and secret from [here](https://github.com/settings/developers)
* Github token from [here](https://github.com/settings/tokens)
* Bintray API key from [here](https://bintray.com/profile/edit) -> _API Key_
* Kitware GitLab token from [here](https://gitlab.kitware.com/profile/personal_access_tokens)

**Note:** You currently need ALL of these in order to run the generator

Then put them in environment variables before running the generator:

* `GITHUB_CLIENT_ID`
* `GITHUB_CLIENT_SECRET`
* `GITHUB_TOKEN`
* `BINTRAY_API_KEY`
* `BINTRAY_USERNAME`
* `GITLAB_GITLAB_KITWARE_COM_TOKEN`

#### Running the generator

```commandline
mkdir build && cd build
python conan_inquiry.py generate
```

### Developing the web interface

Copy a generated `packages.js` to `conan_inquiry/data/web` and open `index.html` in your browser of choice.

## Contributing

Please read [CONTRIBUTING.md](https://github.com/02JanDal/conan_inquiry/blob/master/CONTRIBUTING.md) for details on our
code of conduct, and the process for submitting pull requests.

## Authors

* [Jan Dalheimer](https://github.com/02JanDal) - Initial work and maintainer

See also the list of [contributors](https://github.com/02JanDal/conan_inquiry/contributors) for everyone who
participated in this project.

## License

This project is licensed under the MIT License - see the
[LICENSE](https://github.com/02JanDal/conan_inquiry/blob/master/LICENSE.md) file for details.

## Acknowledgments

* Everyone who has contributed to the [conan project](https://github.com/conan-io/conan)
* @PurpleBooth for the [README template](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)