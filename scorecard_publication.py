"""Publish a matched ledger, scorecard and README in one Git commit."""

from github import InputGitTreeElement

from honest_scorecard import build_scorecard_text, json_text, replace_headline


def publish_snapshot(repo, ref, parent, readme, ledger_text, scorecard):
    """Refuse inconsistent artifacts; a concurrent branch advance must not be forced."""
    if build_scorecard_text(ledger_text) != scorecard:
        raise ValueError("Scorecard does not describe the supplied outcome ledger")
    if replace_headline(readme, scorecard) != readme:
        raise ValueError("README does not describe the supplied scorecard")
    contents = {"README.md": readme, "outcomes.csv": ledger_text,
                "signals/scorecard.json": json_text(scorecard)}
    tree = repo.create_git_tree([
        InputGitTreeElement(path, "100644", "blob", content=content)
        for path, content in contents.items()
    ], base_tree=parent.tree)
    if tree.sha == parent.tree.sha:
        return parent.sha
    commit = repo.create_git_commit("Update matched outcome ledger and episode scorecard", tree, [parent])
    ref.edit(commit.sha, force=False)
    return commit.sha
