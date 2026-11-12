"""Offline regression checks for channel selection and matched publication."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import pandas as pd

import honest_scorecard as hs
from scorecard_publication import publish_snapshot


def calls(rows):
    return pd.DataFrame(rows, columns=["call_date", "market", "signal_type", "quadrant", "status"])


def fixture():
    return calls([
        ("2026-01-01", "Silver", "CRITICAL", "Q1", "true_positive"),
        ("2026-01-02", "Silver", "Q4", "Q4", "false_positive"),
        ("2026-01-03", "Silver", "CRITICAL", "Q2", "pending"),
    ])


class ChannelTests(unittest.TestCase):
    def test_other_channel_success_cannot_credit_q4(self):
        episodes = hs.channel_episodes(fixture())
        self.assertEqual(episodes[hs.CHANNELS[0]].iloc[0]["outcome"], "FP")
        self.assertEqual(episodes[hs.CHANNELS[1]].iloc[0]["outcome"], "TP")
        self.assertEqual(episodes[hs.CHANNELS[0]].iloc[0]["n_calls"], 1)

    def test_other_channel_pending_cannot_censor_q4(self):
        episodes = hs.channel_episodes(fixture().iloc[1:])
        self.assertEqual(episodes[hs.CHANNELS[0]].iloc[0]["outcome"], "FP")
        self.assertEqual(episodes[hs.CHANNELS[1]].iloc[0]["outcome"], "OPEN")

    def test_other_channel_success_cannot_resolve_pending_q4(self):
        df = fixture()
        df.loc[1, "status"] = "pending"
        result = hs.score(hs.channel_episodes(df))["channels"][hs.CHANNELS[0]]
        self.assertEqual((result["tp"], result["resolved"], result["open_censored"]), (0, 0, 1))

    def test_non_q4_bridge_cannot_join_q4_episodes(self):
        df = calls([
            ("2026-01-01", "X", "Q4", "Q4", "false_positive"),
            ("2026-01-20", "X", "CRITICAL", "Q1", "pending"),
            ("2026-02-10", "X", "Q4", "Q4", "false_positive"),
        ])
        result = hs.score(hs.channel_episodes(df))["channels"]
        self.assertEqual(result[hs.CHANNELS[0]]["episodes"], 2)
        self.assertEqual(result[hs.CHANNELS[0]]["fp"], 2)
        self.assertEqual(result[hs.CHANNELS[1]]["episodes"], 1)

    def test_q4_channel_endpoints_are_its_own(self):
        episode = hs.channel_episodes(fixture())[hs.CHANNELS[0]].iloc[0]
        self.assertEqual((episode["start"], episode["end"]), ("2026-01-02", "2026-01-02"))

    def test_market_and_gap_boundaries(self):
        df = calls([
            ("2026-01-01", "A", "Q4", "Q4", "false_positive"),
            ("2026-01-31", "A", "Q4", "Q4", "false_positive"),
            ("2026-03-03", "A", "Q4", "Q4", "pending"),
            ("2026-01-31", "B", "Q4", "Q4", "true_positive"),
        ])
        self.assertEqual(hs.merge_episodes(df)["n_calls"].tolist(), [2, 1, 1])

    def test_both_retained_q4_labels_are_supported(self):
        df = fixture()
        df.loc[0, "quadrant"] = "Q4"
        df.loc[1, "quadrant"] = ""
        self.assertEqual(hs.channel_episodes(df)[hs.CHANNELS[0]]["n_calls"].sum(), 2)

    def test_success_precedence_is_explicit_within_channel(self):
        df = fixture()
        df["signal_type"] = "Q4"
        self.assertEqual(hs.channel_episodes(df)[hs.CHANNELS[0]].iloc[0]["outcome"], "TP")

    def test_empty_ledger(self):
        result = hs.build_scorecard_text(fixture().iloc[:0].to_csv(index=False))
        for channel in result["channels"].values():
            self.assertEqual(channel["episodes"], 0)
            self.assertIsNone(channel["precision_resolved_only"])
        self.assertIsNone(result["source"]["latest_call_date"])

    def test_row_order_does_not_change_episodes(self):
        a = hs.channel_episodes(fixture())
        b = hs.channel_episodes(fixture().iloc[::-1])
        for name in hs.CHANNELS:
            pd.testing.assert_frame_equal(a[name], b[name])

    def test_unknown_status_refused(self):
        df = fixture()
        df.loc[0, "status"] = "misspelled"
        with self.assertRaisesRegex(ValueError, "Unknown outcome"):
            hs.channel_episodes(df)

    def test_unknown_signal_type_refused(self):
        df = fixture()
        df.loc[0, "signal_type"] = "ELEVATED"
        with self.assertRaisesRegex(ValueError, "CRITICAL/Q4"):
            hs.channel_episodes(df)

    def test_missing_dates_and_markets_refused(self):
        for column in ("market", "call_date"):
            df = fixture()
            df.loc[0, column] = None
            with self.subTest(column=column), self.assertRaises(ValueError):
                hs.channel_episodes(df)

    def test_legacy_mixed_episode_input_refused(self):
        with self.assertRaisesRegex(ValueError, "independently"):
            hs.score(hs.merge_episodes(fixture()))


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "outcomes.csv").write_text(fixture().to_csv(index=False), encoding="utf-8")
        (self.root / "README.md").write_text("# Title\n\n**Episode hit rate (resolved-only): old**\n\nTail\n", encoding="utf-8")
        hs.sync_artifacts(self.root)

    def test_repeatable_and_check_does_not_write(self):
        paths = [self.root / "README.md", self.root / "signals/scorecard.json"]
        before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
        hs.sync_artifacts(self.root, check=True)
        self.assertEqual(before, [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths])
        hs.sync_artifacts(self.root)
        self.assertEqual([x[0] for x in before], [p.read_bytes() for p in paths])

    def test_stale_json_refused(self):
        (self.root / "signals/scorecard.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Stale"):
            hs.sync_artifacts(self.root, check=True)

    def test_stale_readme_refused(self):
        path = self.root / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("1/1 (100%)", "9/9 (100%)"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Stale"):
            hs.sync_artifacts(self.root, check=True)

    def test_changed_ledger_refused_even_if_counts_unchanged(self):
        path = self.root / "outcomes.csv"
        path.write_text(path.read_text(encoding="utf-8").replace("Silver", "Gold"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Stale"):
            hs.sync_artifacts(self.root, check=True)

    def test_cross_platform_source_digest(self):
        text = fixture().to_csv(index=False, lineterminator="\n")
        self.assertEqual(hs.build_scorecard_text(text), hs.build_scorecard_text(text.replace("\n", "\r\n")))

    def test_marker_errors_are_not_silently_repaired(self):
        sc = hs.build_scorecard(self.root / "outcomes.csv")
        for readme in ("# Missing", hs.START, hs.END + hs.START, hs.markdown_headline(sc) * 2):
            with self.subTest(readme=readme), self.assertRaises(ValueError):
                hs.replace_headline(readme, sc)

    def test_committed_artifacts_are_current(self):
        hs.sync_artifacts(check=True)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.text = fixture().to_csv(index=False)
        self.sc = hs.build_scorecard_text(self.text)
        self.readme = "# Test\n" + hs.markdown_headline(self.sc)
        self.repo, self.ref, self.parent = Mock(), Mock(), Mock()
        self.parent.sha = "parent"
        self.parent.tree.sha = "old-tree"
        self.repo.create_git_tree.return_value.sha = "new-tree"
        self.repo.create_git_commit.return_value.sha = "new-commit"

    def publish(self):
        return publish_snapshot(self.repo, self.ref, self.parent, self.readme, self.text, self.sc)

    def test_three_artifacts_share_one_commit(self):
        self.assertEqual(self.publish(), "new-commit")
        elements = self.repo.create_git_tree.call_args.args[0]
        content = {element._identity["path"]: element._identity["content"] for element in elements}
        self.assertEqual(set(content), {"README.md", "outcomes.csv", "signals/scorecard.json"})
        self.assertEqual(json.loads(content["signals/scorecard.json"]), hs.build_scorecard_text(content["outcomes.csv"]))
        self.repo.create_git_commit.assert_called_once()
        self.assertEqual(self.repo.create_git_commit.call_args.args[2], [self.parent])
        self.ref.edit.assert_called_once_with("new-commit", force=False)

    def test_stale_input_refused_before_remote_mutation(self):
        self.sc["calls"]["pending"] = 99
        with self.assertRaisesRegex(ValueError, "ledger"):
            self.publish()
        self.repo.create_git_tree.assert_not_called()

    def test_stale_readme_refused_before_remote_mutation(self):
        self.readme = self.readme.replace("1/1 (100%)", "9/9 (100%)")
        with self.assertRaisesRegex(ValueError, "README"):
            self.publish()
        self.repo.create_git_tree.assert_not_called()

    def test_concurrent_update_is_not_forced_or_retried(self):
        self.ref.edit.side_effect = RuntimeError("non-fast-forward")
        with self.assertRaisesRegex(RuntimeError, "non-fast-forward"):
            self.publish()
        self.ref.edit.assert_called_once_with("new-commit", force=False)

    def test_unchanged_tree_does_not_commit(self):
        self.repo.create_git_tree.return_value.sha = "old-tree"
        self.assertEqual(self.publish(), "parent")
        self.repo.create_git_commit.assert_not_called()
        self.ref.edit.assert_not_called()

    def test_updater_uses_one_snapshot_and_pinned_readme(self):
        import update_lambda as updater
        from io import StringIO
        repo = self.repo
        repo.default_branch = "main"
        repo.get_git_ref.return_value = self.ref
        self.ref.object.sha = "parent"
        repo.get_git_commit.return_value = self.parent
        repo.get_contents.return_value.decoded_content = b"<!-- LAMBDA_START -->old<!-- LAMBDA_END -->"
        with patch.object(updater, "GITHUB_TOKEN", "test-only"), patch.object(updater, "GITHUB_REPO", "fixture/repo"), \
                patch.object(updater, "Github") as github, patch("builtins.open", return_value=StringIO(self.text)), \
                patch.object(updater, "generate_table", return_value=hs.markdown_headline(self.sc)) as table:
            github.return_value.get_repo.return_value = repo
            self.assertTrue(updater.update_github_readme([]))
        repo.get_contents.assert_called_once_with("README.md", ref="parent")
        table.assert_called_once_with([], scorecard=self.sc)
        self.ref.edit.assert_called_once_with("new-commit", force=False)

    def test_regeneration_failure_has_no_old_scorecard_fallback(self):
        import update_lambda as updater
        with patch.object(hs, "build_scorecard", side_effect=ValueError("bad ledger")):
            with self.assertRaisesRegex(ValueError, "bad ledger"):
                updater.refresh_honest_scorecard()


if __name__ == "__main__":
    unittest.main()
