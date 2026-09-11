import json

from project_indexer import ProjectIndexer


def test_detects_js_and_json_structure(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.js").write_text(
        "class User {\n"
        "  constructor(name) { this.name = name; }\n"
        "}\n\n"
        "function greet(name) {\n"
        "  return 'hi ' + name;\n"
        "}\n\n"
        "const value = 42;\n",
        encoding="utf-8",
    )
    (project / "config.json").write_text(
        json.dumps({"apiKey": "demo", "features": {"beta": True}}),
        encoding="utf-8",
    )

    indexer = ProjectIndexer(str(project))
    result = indexer.inspect_file_structure("app.js")

    assert result["language"] == "javascript"
    assert any(item["name"] == "User" and item["kind"] == "class" for item in result["symbols"])
    assert any(item["name"] == "greet" and item["kind"] == "function" for item in result["symbols"])

    json_result = indexer.inspect_file_structure("config.json")
    assert json_result["language"] == "json"
    assert "apiKey" in json_result["keys"]
    assert "features" in json_result["keys"]


def test_detects_html_and_css_structure(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "index.html").write_text(
        "<main><section class='card'><button id='save'>Save</button></section></main>",
        encoding="utf-8",
    )
    (project / "styles.css").write_text(
        ".card { color: red; }\n#save { padding: 8px; }\n",
        encoding="utf-8",
    )

    indexer = ProjectIndexer(str(project))
    html_result = indexer.inspect_file_structure("index.html")
    css_result = indexer.inspect_file_structure("styles.css")

    assert html_result["language"] == "html"
    assert "main" in html_result["tags"]
    assert "section" in html_result["tags"]

    assert css_result["language"] == "css"
    assert ".card" in css_result["selectors"]
    assert "#save" in css_result["selectors"]
