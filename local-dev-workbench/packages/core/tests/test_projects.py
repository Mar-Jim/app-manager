import yaml

from dev_workbench.projects import create_project


def test_bundle_job_generator_creates_expected_files(tmp_path):
    result = create_project(kind="bundle-job", name="demo-job", output_dir=tmp_path)

    root = tmp_path / "demo-job"
    assert result["created"] is True
    assert (root / "databricks.yml").exists()
    assert (root / "resources/job.yml").exists()
    assert (root / "src/jobs/main.py").exists()
    assert (root / "tests/test_placeholder.py").exists()
    assert (root / "README.md").exists()
    assert (root / ".gitignore").exists()


def test_bundle_pipeline_generator_creates_expected_files(tmp_path):
    create_project(kind="bundle-pipeline", name="demo-pipeline", output_dir=tmp_path)

    root = tmp_path / "demo-pipeline"
    assert (root / "databricks.yml").exists()
    assert (root / "resources/pipeline.yml").exists()
    assert (root / "src/pipelines/pipeline.py").exists()
    assert (root / "tests/test_placeholder.py").exists()
    assert (root / "README.md").exists()


def test_bundle_sql_generator_creates_expected_files(tmp_path):
    create_project(kind="bundle-sql", name="demo-sql", output_dir=tmp_path)

    root = tmp_path / "demo-sql"
    assert (root / "databricks.yml").exists()
    assert (root / "resources/sql.yml").exists()
    assert (root / "sql/001_create_tables.sql").exists()
    assert (root / "tests/test_placeholder.py").exists()
    assert (root / "README.md").exists()


def test_bundle_dashboard_generator_creates_expected_files(tmp_path):
    create_project(kind="bundle-dashboard", name="demo-dashboard", output_dir=tmp_path)

    root = tmp_path / "demo-dashboard"
    assert (root / "databricks.yml").exists()
    assert (root / "resources/dashboard.yml").exists()
    assert (root / "dashboards/README.md").exists()
    assert (root / "README.md").exists()
    assert "workspace-specific implementation" in (root / "resources/dashboard.yml").read_text(encoding="utf-8")


def test_no_overwrite_without_force(tmp_path):
    create_project(kind="bundle-sql", name="demo-sql", output_dir=tmp_path)
    databricks_file = tmp_path / "demo-sql/databricks.yml"
    databricks_file.write_text("existing: true\n", encoding="utf-8")

    result = create_project(kind="bundle-sql", name="demo-sql", output_dir=tmp_path)

    assert result["created"] is False
    assert "databricks.yml" in result["conflicts"]
    assert databricks_file.read_text(encoding="utf-8") == "existing: true\n"


def test_generated_databricks_yml_only_includes_dev_target(tmp_path):
    create_project(kind="bundle-pipeline", name="demo-pipeline", output_dir=tmp_path)

    bundle = yaml.safe_load((tmp_path / "demo-pipeline/databricks.yml").read_text(encoding="utf-8"))

    assert list(bundle["targets"]) == ["dev"]


def test_external_deployer_note_is_included_in_readme(tmp_path):
    create_project(kind="bundle-dashboard", name="demo-dashboard", output_dir=tmp_path)

    readme = (tmp_path / "demo-dashboard/README.md").read_text(encoding="utf-8")

    assert "external deployer repo" in readme
    assert "Deployment strategy: `external-deployer`" in readme


def test_github_action_is_optional(tmp_path):
    create_project(kind="bundle-job", name="without-action", output_dir=tmp_path)
    create_project(kind="bundle-job", name="with-action", output_dir=tmp_path, include_github_action=True)

    assert not (tmp_path / "without-action/.github/workflows/bundle-validate.yml").exists()
    workflow = tmp_path / "with-action/.github/workflows/bundle-validate.yml"
    assert workflow.exists()
    assert "databricks bundle validate -t dev" in workflow.read_text(encoding="utf-8")
