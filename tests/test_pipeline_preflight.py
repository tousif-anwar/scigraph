from pathlib import Path

from scigraph.preprocessing import pipeline


def test_find_java_executable_uses_java_home(monkeypatch, tmp_path: Path) -> None:
    java_dir = tmp_path / "jdk" / "bin"
    java_dir.mkdir(parents=True)
    java_exe = java_dir / "java.exe"
    java_exe.write_text("", encoding="utf-8")

    monkeypatch.setenv("JAVA_HOME", str(tmp_path / "jdk"))
    monkeypatch.setattr(pipeline.shutil, "which", lambda _: None)

    assert pipeline.find_java_executable() == str(java_exe)


def test_find_java_executable_uses_config(tmp_path: Path) -> None:
    java_dir = tmp_path / "jdk" / "bin"
    java_dir.mkdir(parents=True)
    java_exe = java_dir / "java.exe"
    java_exe.write_text("", encoding="utf-8")

    assert pipeline.find_java_executable({"spark": {"java_home": str(tmp_path / "jdk")}}) == str(
        java_exe
    )


def test_find_java_executable_returns_none_without_java(monkeypatch) -> None:
    monkeypatch.delenv("JAVA_HOME", raising=False)
    monkeypatch.setattr(pipeline.shutil, "which", lambda _: None)

    assert pipeline.find_java_executable() is None


def test_configure_runtime_environment_sets_hadoop_home(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "project"
    hadoop_bin = root / "tools" / "hadoop" / "bin"
    hadoop_bin.mkdir(parents=True)
    (hadoop_bin / "winutils.exe").write_text("", encoding="utf-8")
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("HADOOP_HOME", raising=False)

    config = {
        "_project_root": str(root),
        "spark": {"hadoop_home": "tools/hadoop"},
    }

    pipeline.configure_runtime_environment(config)

    assert pipeline.os.environ["HADOOP_HOME"] == str(root / "tools" / "hadoop")
    assert str(hadoop_bin) in pipeline.os.environ["PATH"]
