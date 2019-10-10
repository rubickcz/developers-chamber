import re
import subprocess

from developers_chamber.scripts import cli
from developers_chamber.utils import print_bold, print_error, print_heading, print_success
from git import Repo


class QAError(Exception):
    def __init__(self, msg, output):
        super().__init__(msg)
        self.output = output.strip()


class QACheck:
    """
    Base class for a quality assurance check.

    Arguments:
        name: Name of the check.
    """
    name = None

    def _get_repo(self):
        """
        Returns the repo object.
        """
        return Repo('.')

    def _get_default_branch(self):
        """
        Returns default branch of the repo.
        """
        return self._run_command("git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'")

    def _get_diffs(self):
        """
        Returns Git diffs against default branch.
        """
        repo = self._get_repo()
        target_branch = getattr(repo.remotes.origin.refs, self._get_default_branch())
        target_commit = repo.merge_base(repo.active_branch, target_branch)[0]
        return target_commit.diff(repo.active_branch.name, create_patch=True)

    def _get_unstaged(self):
        """
        Returns unstaged files in the repo.
        """
        return self._get_repo().index.diff(None, create_patch=True)

    def _run_command(self, command):
        """
        Runs shell command and returns its output.
        """
        try:
            return subprocess.check_output(command, shell=True).decode().strip()
        except subprocess.CalledProcessError as ex:
            raise QAError(str(ex), ex.output.decode())

    def _run_check(self):
        """
        This function should implement the actual check and should raise `QAError` if failed.
        """
        raise NotImplementedError()

    def _cleanup(self):
        """
        Cleans up the repo to be fresh for another check.
        """
        self._get_repo().git.stash('save')

    def run(self):
        """
        Runs the check and cleanup methods.
        """
        self._run_check()
        self._cleanup()


class QACheckRunner:
    """
    Runs multiple checks and evaluates the results while printing a nice output.
    """
    def __init__(self, *checks):
        """
        Arguments:
            checks: Instances of QACheck class.
        """
        self.checks = checks

    def run(self):
        print('-----------------------------------------------------------')
        print_bold(' Quality Assurance Check')
        print('-----------------------------------------------------------')

        failed_checks = []
        for i, check in enumerate(self.checks):
            print_heading('[{}/{}] {}...'.format(i + 1, len(self.checks), check.name))
            try:
                check.run()
            except QAError as ex:
                failed_checks.append(check)
                print_error(ex)
                print(ex.output)
            else:
                print_success('OK')

        print('-----------------------------------------------------------')

        if failed_checks:
            print_error('FAILURE: {} check(s) failed!'.format(len(failed_checks)))
            exit_code = 1
        else:
            print_success('SUCCESS: All QA checks passed!')
            exit_code = 0

        print('-----------------------------------------------------------')
        exit(exit_code)


# Specific QA Checks
# ----------------------------------------------------------------------------------------------------------------------


class MissingMigrationsQACheck(QACheck):
    """
    Checks that make migrations command does not generate new migrations.
    """
    name = 'Check missing migrations'

    def _run_check(self):
        output = self._run_command('pydev make-migration --dry-run')
        last_line = output.split('\n')[-1]
        if last_line != 'No changes detected':
            raise QAError('Found missing migration(s)!', output)


class MigrationFilenamesQACheck(QACheck):
    """
    Checks that new migrations introduced in the branch have correct names.
    """
    name = 'Check migration filenames'

    def _is_migration_file_with_wrong_name(self, path):
        match = re.search(r'migrations\/([^\/]+)\.py$', path)
        return bool(match and not re.search(r'^[0-9]{4}$', match.group(1)))

    def _run_check(self):
        wrong_name_files = []
        for diff in self._get_diffs():
            if diff.new_file and self._is_migration_file_with_wrong_name(diff.b_path):
                wrong_name_files.append(diff.b_path)

        if wrong_name_files:
            raise QAError('Found wrongly named migration file:', '\n'.join(wrong_name_files))


class MissingTranslationsQACheck(QACheck):
    """
    Checks that generating translations does not introduce any changes.
    """
    name = 'Check missing translations'

    def _is_translation_file(self, path):
        return bool(re.search(r'django\.po$', path))

    def _run_check(self):
        self._run_command('pydev make-msgs')

        translation_files = []
        for diff in self._get_unstaged():
            diff_string = diff.diff.decode()
            if self._is_translation_file(diff.b_path) and re.findall(r'(\+|-)(msgstr|msgid)', diff_string):
                translation_files.append((diff.b_path, diff_string))

        if translation_files:
            raise QAError('Found changes in following translation file(s):', '\n'.join(
                '{}\n{}'.format(file, diff) for file,diff in translation_files)
            )


class ImportOrderQACheck(QACheck):
    """
    Checks that isort applied on changed files does not introduce any changes.
    """
    name = 'Check import order'

    def _is_python_file(self, path):
        return bool(re.search(r'\.py$', str(path)))

    def _run_check(self):
        changed_files = [diff.b_path for diff in self._get_diffs() if self._is_python_file(diff.b_path)]
        if changed_files:
            self._run_command('isort {}'.format(' '.join(changed_files)))
        else:
            return

        wrong_import_order_files = set(changed_files) & set([diff.b_path for diff in self._get_unstaged()])
        if wrong_import_order_files:
            raise QAError('Found unsorted import(s) in following files:', '\n'.join(wrong_import_order_files))


# CLI commands
# ---------------------------------------------------------------------------------------------------------------------


@cli.group()
def qa():
    """
    Quality assurance commands.
    """

@qa.command()
def all():
    """
    Runs all defined QA checks.
    """
    QACheckRunner(*(qa_check() for qa_check in QACheck.__subclasses__())).run()


@qa.command()
def missing_migrations():
    """
    Runs missing migrations QA check.
    """
    QACheckRunner(MissingMigrationsQACheck()).run()


@qa.command()
def migration_filenames():
    """
    Runs migration filenames QA check.
    """
    QACheckRunner(MigrationFilenamesQACheck()).run()


@qa.command()
def missing_translations():
    """
    Runs missing translations QA check.
    """
    QACheckRunner(MissingTranslationsQACheck()).run()


@qa.command()
def import_order():
    """
    Runs import order QA check.
    """
    QACheckRunner(ImportOrderQACheck()).run()
