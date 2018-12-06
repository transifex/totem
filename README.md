TemCheck
--------

TemCheck is a Git Health Check library that checks whether or not certain quality standards are followed on pull requests or local Git repositories.

It was created in order to automate the Git-related checks defined in the [Transifex Engineering Manifesto](https://tem.transifex.com/).

Currently it supports Github pull requests only.


# Features
- Perform multiple checks on a PR level (pull request, commits, etc)
- Perform multiple checks on local Git repositories, suitable as a pre-push hook
- Configurable: you can only enable the checks you want, and define the configuration parameters for each check, so you can apply the tool to various repositories with different options
- Detailed report in the console, makes it easy to spot any issues
- Ability for a useful summary, shown as a comment created on the pull request with configurable content (disabled by default)  


# Installation
TemCheck can be installed by running `pip install git+ssh://git@github.com/transifex/temcheck.git@master`. It requires Python 3.6.0+.


# Usage

## Running on a PR
### Command line
TemCheck provides a console command and requires only the URL of the pull request to check. 
By default, it will attempt to read the `.temcheck.yml` file on the repo as configuration. If it is not found, it defaults to `./contrib/config/sample.yml` on the temcheck repo.

```
temcheck -p https://www.github.com/:owner/:repo/pulls/:number
```

NOTE: the default configuration will *not* create a comment on the pull request being checked. Therefore, you can test in at will on various public projects. If you use a custom config, make sure you know what you are doing if you are hitting public projects.   

A custom config can be provided and supports a lot of options.

```
temcheck -p https://www.github.com/:owner/:repo/pulls/:number -c ./temcheck_config.yml
```

The project includes a sample configuration file, which can be found at `./contrib/config/sample.yml`.

### CI
When running from a CI service, you need to retrieve the pull request URL from the environment variables the service provides. Also, you can set the URL of the CI build page, in which case a link appears on the PR comment that the TemCheck creates.

For example, with CircleCI you need to make the following call:
```
temcheck --pr-url $CIRCLE_PULL_REQUEST --config-file .circleci/temcheck.yml --details-url $CIRCLE_BUILD_URL
```

## Running on a local repository

You can call the command without any arguments. In this case it reads the `.temcheck.yml` file on the repo as configuration. If this file does not exist, the tool cannot run.
```
temcheck
```

You can also define a custom config file to use.
```
temcheck -c <file>
```

### Pre-push hook

In order to use it as a pre-push hook, add the following in the `.git/hooks/pre-push` file:
```
#!/bin/sh
temcheck
```

Note: Make sure the file is executable (`chmod +x .git/hooks/pre-push`).

This way, temcheck will run every time you call `git push`, and will abort the command in case any checks fail. Note that it will not abort in case of warnings.

## Github authentication
In order to run TemCheck on pull requests of private projects, as well as in order to be able to enable reporting in PR comments, the tool needs to be authenticated when contacting Github. In order to do that, all you have to do is to add an environment variable with the Github access token:
`GITHUB_ACCESS_TOKEN='<my_super_secret_token>`


# Checks

TemCheck supports the following checks:

- **branch_name**: the name of the branch must follow a certain regex pattern
- **pr_title**: the title of the pull request must follow a certain regex pattern
- **pr_body_checklist**: the body of the pull request must not contain any unfinished checklist item
- **pr_body_excludes**: the body of the pull request must not contain certain strings
- **pr_body_includes**: the body of the pull request must contain certain strings
- **commit_message**: the message of each commit must follow these guidelines:
  * subject:
    * has a minimum and maximum allowed length
    * must start with an uppercase character and *not* end with a '.'
  * body
    * if there is a body, each line has a maximum allowed length
    * if the commit has a lot of changes, a body must be present and must have a minimum number of lines

With a custom configuration, you can selected which checks will be executed. All of the checks have at least a certain level of configuration.  

## Failure level
If a check is executed but fails to pass, it can either provide a failed status check or simply print out a warning. The former can be used in order to prevent a pull request from being merged until all TemCheck checks are fixed. 

The latter is mainly used as a heads up for reviewers of the PR and is necessary because in some projects a rule may not be always applicable.  


# Configuration
This is a sample configuration that contains all available options:

```yaml
settings:
  pr_comment_report:
    enabled: True
    show_empty_sections: True
    show_message: True
    show_details: True
  console_report:
    show_empty_sections: True
    show_message: True
    show_details: True
    show_successful: True
  local_console_report:
    show_empty_sections: False
    show_message: True
    show_details: True
    show_successful: False
checks:
  branch_name:
    pattern: ^[\w\d\-]+$
    pattern_descr: Branch name must only include lowercase characters, digits and dashes
    failure_level: warning
  pr_title:
    pattern: ^[A-Z].+$
    pattern_descr: PR title must start with a capital letter
    failure_level: warning
  pr_body_checklist:
    failure_level: error
  pr_body_excludes:
    patterns:
    - excl1
    - excl2
    failure_level: error
  pr_body_includes:
    patterns:
    - incl1
    - incl2
    failure_level: error
  commit_message:
    subject:
      min_length: 10
      max_length: 50
      pattern: ^[A-Z].+(?<!\.)$
      pattern_descr: Commit message subject must start with a capital letter and not
        finish with a dot
    body:
      max_line_length: 72
      smart_require:
        min_changes: 100
        min_body_lines: 1
    failure_level: error
```

# Sample report
This is how a report created as a comment on the pull request may look like:

Checking if this PR follows the expected quality standards. Powered by [temcheck](https://www.github.com/transifex/temcheck).

failures | warnings | successful
----------- | ------------- | -------------
| 0 | 0 | 3



:bangbang: **Failures (2)** - *These need to be fixed!*
- **pr_body_includes**
  Required strings in PR body are missing: `"Problem and/or solution"`
- **commit_message**
  Found 2 commit message(s) that do not follow the expected format (errors: `"smart_body_size"`, `"subject_pattern"`, `"subject_length"`)
  errors:
  - commit_order: 1
    sha: fda892cf64cd2f47285bc368aa892d0d6c134caa
    smart_body_size: 'There are more than 15 changes in total on this commit, so the
      commit message body should be at least 2 lines long, but it is 0 instead'
    url: https://github.com/owner/repo/commit/fda892cf64cd2f47285bc368aa892d0d6c134caa
  - commit_order: 2
    sha: ceb9696937b19ee2cda96c968800596b45280b1e
    subject_length: 'Subject has 1 characters but should be between 10 and 50'
    subject_pattern: 'Subject does not follow pattern: `"^[A-Z].+(?<!\.)$"`. Explanation:
      Commit message subject must start with a capital letter and not finish with
      a dot'
    url: https://github.com/owner/repo/commit/ceb9696937b19ee2cda96c968800596b45280b1e


:eight_pointed_black_star: **Warnings (1)** - *Fixing these may not be applicable, please review them case by case*
- **pr_title**
  PR title `"Fix things"` does not match pattern: `"^XX-[0-9]+ .+$"`. 
  Explanation: PR title must start with the Jira ID

:white_check_mark: **Successful (3)** - *Good job on these!*
- **branch_name**
- **pr_body_checklist**
- **pr_body_excludes**
