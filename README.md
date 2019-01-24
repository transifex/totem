Totem
-----

Totem is a Health Check library that checks whether or not certain quality standards are followed on Pull Requests or local Git repositories.

It is inspired by the [Transifex Engineering Manifesto (TEM)](https://tem.transifex.com/), a document that defines the Quality Standards used in Transifex. Totem was created as an automated way to ensure high quality in Git-related guidelines described in the TEM. 

Currently it supports Github Pull Requests only.


# Features
- Multiple quality checks on a Pull Request
- Multiple quality checks on local Git repositories 
- Comes with pre-commit support, and can also be added as a pre-push Git hook
- Configurable: you can only enable the checks you want, and define the configuration parameters for each check, so you can apply the tool to various repositories with different options on each
- Detailed report in the console, makes it easy to spot issues
- Ability for a useful summary shown as a comment created on the Pull Request with configurable content (disabled by default)  


# Checks

Totem supports the following checks:

- **branch_name**: the name of the branch must follow a certain regex pattern
- **pr_title**: the title of the Pull Request must follow a certain regex pattern
- **pr_body_checklist**: the body of the Pull Request must not contain any unfinished checklist item
- **pr_body_excludes**: the body of the Pull Request must not contain certain strings
- **pr_body_includes**: the body of the Pull Request must contain certain strings
- **commit_message**: the message of each commit must follow these guidelines:
  * subject:
    * has a minimum and maximum allowed length
    * must start with an uppercase character and *not* end with a '.'
  * body
    * if there is a body, each line has a maximum allowed length
    * if the commit has a lot of changes, a body must be present and must have a minimum number of lines

With a custom configuration, you can define which checks will be executed. All of the checks have at least a certain level of configuration.  

## Failure level
If a check is executed but fails to pass, it can either provide a failed status check (exit status = 1) or simply print out a warning.
The former can be used in order to prevent a Pull Request from being merged, a local commit to be completed, or local changes to be pushed to the remote, until all Totem checks are fixed.
The latter is mainly used as a sign that something might not be right, and can be useful when comitting in or pushing from a local repo, or when reviewing a Pull Request. The warning level is necessary because in some repos a rule may not be always applicable, so it should be judged on a case-by-case basis.  


# Installation & Usage
Totem can be installed by running `pip install git+ssh://git@github.com/transifex/totem.git@master` (soon to be on PyPi). It requires Python 3.6.0+.

## Running on a PR
### Command line
Totem provides a console command and requires only the URL of the pull request to check. 
By default, it will attempt to read the `.totem.yml` file on the repo as configuration. If it is not found, it defaults to `./contrib/config/sample.yml` on the Totem repo.

```
totem -p https://www.github.com/:owner/:repo/pulls/:number
```

NOTE: the default configuration will *not* create a comment on the Pull Request being checked. If you use a custom config, you can enable the comment feature.   

A custom config can be provided and supports a lot of options.

```
totem -p https://www.github.com/:owner/:repo/pulls/:number -c ./totem_config.yml
```

The project includes a sample configuration file, which can be found at `./contrib/config/sample.yml`.

### CI
When running from a CI service, you need to retrieve the pull request URL from the environment variables the service provides. Also, you can set the URL of the CI build page, in which case a link appears on the PR comment that the Totem creates.

For example, with CircleCI you need to make the following call:
```
totem --pr-url $CIRCLE_PULL_REQUEST --config-file .totem.yml --details-url $CIRCLE_BUILD_URL
```

## Running on a local repository

You can call the command without any arguments. In this case it reads the `.totem.yml` file on the repo as configuration. If this file does not exist, the tool cannot run.
```
totem
```

You can also define a custom config file to use.
```
totem -c <file>
```

### Pre-push hook

In order to use it as a pre-push hook, add the following in the `.git/hooks/pre-push` file:
```
#!/bin/sh
totem
```

Note: Make sure the file is executable (`chmod +x .git/hooks/pre-push`).

This way, totem will run every time you call `git push`, and will abort the command in case any checks fail. Note that it will not abort in case of warnings.

## Github authentication
In order to run Totem on pull requests of private projects, as well as in order to be able to enable reporting in PR comments, the tool needs to be authenticated when contacting Github. In order to do that, all you have to do is to add an environment variable with the Github access token:
`GITHUB_ACCESS_TOKEN=<my_super_secret_token>`


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

Checking if this PR follows the expected quality standards. Powered by [totem](https://www.github.com/transifex/totem).

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
